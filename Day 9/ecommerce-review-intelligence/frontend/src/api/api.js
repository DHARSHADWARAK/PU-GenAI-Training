const BASE_URL = "http://127.0.0.1:8000";

export const fetchProducts = async () => {
  const res = await fetch(`${BASE_URL}/products`);
  return res.json();
};

export const fetchProduct = async (name) => {
  const res = await fetch(`${BASE_URL}/products/${name}`);
  return res.json();
};