const { getLogger } = require('./logger');
const logger = getLogger('geocode');

async function geocodeAddress(text) {
  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  if (!apiKey) {
    logger.error('GOOGLE_MAPS_API_KEY is not set');
    return null;
  }
  try {
    const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(text)}&key=${apiKey}`;
    const res = await fetch(url);
    if (!res.ok) {
      logger.error(`Geocode request failed: ${res.status}`);
      return null;
    }
    const data = await res.json();
    if (!data.results || !data.results.length) return null;
    const loc = data.results[0].geometry.location;
    return { latitude: loc.lat, longitude: loc.lng };
  } catch (err) {
    logger.error(`Geocode error: ${err.message}`);
    return null;
  }
}

module.exports = { geocodeAddress };
