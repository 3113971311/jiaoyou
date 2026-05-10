// 使用 Nominatim (OpenStreetMap) 免费逆地理编码
// 无需 API Key，但需遵守使用条款（带 User-Agent，请求频率不超过1次/秒）

export async function reverseGeocode(lat: number, lng: number): Promise<{ city: string; province: string }> {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&accept-language=zh`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'FriendChat/1.0 (social-app)' },
    });
    if (!res.ok) throw new Error('geocode failed');
    const data = await res.json() as any;
    const addr = data.address || {};

    // 提取城市和省
    const city = addr.city || addr.town || addr.county || addr.city_district || '';
    const province = addr.state || addr.province || '';

    return { city, province };
  } catch {
    return { city: '', province: '' };
  }
}

export async function forwardGeocode(query: string): Promise<{ lat: number; lng: number } | null> {
  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'FriendChat/1.0 (social-app)' },
    });
    if (!res.ok) return null;
    const data = await res.json() as any[];
    if (data.length === 0) return null;
    return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
  } catch {
    return null;
  }
}
