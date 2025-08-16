const fs = require('fs');
const path = require('path');

const phoneMapPath = path.join(__dirname, 'brandPhones.json');
const phoneMap = JSON.parse(fs.readFileSync(phoneMapPath, 'utf-8'));

function loadBrand(brandId) {
  const filePath = path.join(__dirname, 'brands', `${brandId}.json`);
  const raw = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(raw);
}

function getBrandInfoByPhoneId(phoneNumberId) {
  const entry = phoneMap[phoneNumberId];
  if (!entry) {
    throw new Error(`No brand configured for phone_number_id ${phoneNumberId}`);
  }
  const brandConfig = loadBrand(entry.brand_id);
  return {
    brandConfig,
    phoneNumberId,
    catalogId: entry.catalog_id
  };
}

module.exports = { getBrandInfoByPhoneId };
