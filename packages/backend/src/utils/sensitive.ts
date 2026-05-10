import { prisma } from '../plugins/prisma';

// Trie 树节点
class TrieNode {
  children: Map<string, TrieNode> = new Map();
  isEnd = false;
  level: 'block' | 'replace' = 'replace';
}

// 敏感词 Trie 树
let root: TrieNode | null = null;
let wordsCount = 0;

function buildTrie(words: Array<{ word: string; level: string }>) {
  const node = new TrieNode();
  for (const { word, level } of words) {
    let current = node;
    for (const char of word.toLowerCase()) {
      if (!current.children.has(char)) {
        current.children.set(char, new TrieNode());
      }
      current = current.children.get(char)!;
    }
    current.isEnd = true;
    current.level = level as 'block' | 'replace';
  }
  return node;
}

export async function loadSensitiveWords() {
  const words = await prisma.sensitiveWord.findMany();
  root = buildTrie(words);
  wordsCount = words.length;
  console.log(`已加载 ${wordsCount} 个敏感词`);
}

export function getSensitiveWordsCount() {
  return wordsCount;
}

// 检查文本是否包含敏感词，返回最高处理等级
export function checkText(text: string): { hit: boolean; level: 'block' | 'replace' | null } {
  if (!root) {
    // 未加载时从数据库加载
    console.warn('敏感词库未初始化');
    return { hit: false, level: null };
  }

  const lower = text.toLowerCase();
  let highestLevel: 'block' | 'replace' | null = null;

  for (let i = 0; i < lower.length; i++) {
    let current: TrieNode | undefined = root;
    let j = i;

    while (j < lower.length && current?.children.has(lower[j])) {
      current = current.children.get(lower[j])!;
      j++;
      if (current.isEnd) {
        if (current.level === 'block') {
          return { hit: true, level: 'block' };
        }
        highestLevel = 'replace';
      }
    }
  }

  return { hit: highestLevel !== null, level: highestLevel };
}

// 替换文本中的敏感词为 ***
export function filterText(text: string): string {
  if (!root) return text;

  const lower = text.toLowerCase();
  let result = '';
  let i = 0;

  while (i < text.length) {
    let current: TrieNode | undefined = root;
    let j = i;
    let matchedLen = 0;

    while (j < lower.length && current?.children.has(lower[j])) {
      current = current.children.get(lower[j])!;
      j++;
      if (current.isEnd) {
        matchedLen = j - i;
      }
    }

    if (matchedLen > 0) {
      result += '***';
      i += matchedLen;
    } else {
      result += text[i];
      i++;
    }
  }

  return result;
}
