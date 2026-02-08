"""
Integration tests for the Products API endpoints.
"""


class TestListProducts:
    """Tests for GET /products endpoint."""

    def test_list_products(self, client):
        """Test listing all products."""
        response = client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "products" in data
        assert len(data["products"]) == 3  # Seeded in conftest.py
        
        # Check first product structure
        product = data["products"][0]
        assert "id" in product
        assert "name" in product
        assert "price" in product

    def test_list_products_has_correct_data(self, client):
        """Test that products have correct seeded data."""
        response = client.get("/products")
        products = response.json()["products"]
        
        # Find Web Development product
        web_dev = next(p for p in products if p["name"] == "Web Development")
        assert web_dev["price"] == 1500.0


class TestGetProduct:
    """Tests for GET /products/{id} endpoint."""

    def test_get_product_success(self, client):
        """Test getting a product by ID."""
        response = client.get("/products/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Web Development"
        assert data["price"] == 1500.0

    def test_get_product_not_found(self, client):
        """Test getting non-existent product returns 404."""
        response = client.get("/products/999")
        
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]
