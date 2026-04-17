import { useEffect, useState } from "react";
import { fetchProducts } from "../api/api";
import ProductCard from "../components/ProductCard";

export default function ProductList() {
  const [products, setProducts] = useState({});

  useEffect(() => {
    fetchProducts().then(data => setProducts(data));
  }, []);

  return (
    <div>
      <h1>Products</h1>

      {Object.keys(products).map(name => (
        <ProductCard key={name} product={products[name]} />
      ))}
    </div>
  );
}