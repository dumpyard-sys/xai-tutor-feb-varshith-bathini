"""
Integration tests for the Invoice API endpoints.
"""

import pytest


class TestCreateInvoice:
    """Tests for POST /invoices endpoint."""

    def test_create_invoice_success(self, client, sample_invoice_data):
        """Test successful invoice creation."""
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check invoice fields
        assert data["invoice_no"] == "INV-0001"
        assert data["issue_date"] == "2026-02-08"
        assert data["due_date"] == "2026-03-08"
        
        # Check client info
        assert data["client"]["id"] == 1
        assert data["client"]["name"] == "Acme Corporation"
        
        # Check calculations
        # 2 x Web Development Service ($1500) = $3000
        # 1 x Logo Design ($500) = $500
        # Subtotal = $3500, Tax = $350 (provided), Total = $3850
        assert data["subtotal"] == 3500.0
        assert data["tax"] == 350.0
        assert data["total"] == 3850.0
        
        # Check items
        assert len(data["items"]) == 2
        assert data["items"][0]["quantity"] == 2
        assert data["items"][0]["unit_price"] == 1500.0
        assert data["items"][0]["line_total"] == 3000.0

    def test_create_invoice_uses_client_address_by_default(self, client, sample_invoice_data):
        """Test that invoice uses client's address when not provided."""
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == "123 Business Ave, Suite 100, New York, NY 10001"

    def test_create_invoice_with_custom_address(self, client, sample_invoice_data):
        """Test that invoice can use custom address."""
        sample_invoice_data["address"] = "Custom Billing Address"
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        assert response.json()["address"] == "Custom Billing Address"

    def test_create_invoice_with_zero_tax(self, client, sample_invoice_data):
        """Test invoice creation with zero tax."""
        sample_invoice_data["tax"] = 0.0
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["tax"] == 0.0
        assert data["subtotal"] == 3500.0
        assert data["total"] == 3500.0  # No tax added

    def test_create_invoice_invalid_client(self, client, sample_invoice_data):
        """Test that invalid client ID returns 400 error."""
        sample_invoice_data["client_id"] = 999
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 400
        assert "Client not found" in response.json()["detail"]

    def test_create_invoice_invalid_product(self, client, sample_invoice_data):
        """Test that invalid product ID returns 400 error."""
        sample_invoice_data["items"] = [{"product_id": 999, "quantity": 1}]
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 400
        assert "Product with id 999 not found" in response.json()["detail"]

    def test_create_invoice_empty_items(self, client, sample_invoice_data):
        """Test that empty items list returns 422 validation error."""
        sample_invoice_data["items"] = []
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 422

    def test_create_invoice_missing_required_fields(self, client):
        """Test that missing required fields returns 422 validation error."""
        response = client.post("/invoices", json={})
        assert response.status_code == 422

    def test_create_invoice_sequential_numbers(self, client, sample_invoice_data):
        """Test that invoice numbers are generated sequentially."""
        # Create first invoice
        response1 = client.post("/invoices", json=sample_invoice_data)
        assert response1.json()["invoice_no"] == "INV-0001"
        
        # Create second invoice
        response2 = client.post("/invoices", json=sample_invoice_data)
        assert response2.json()["invoice_no"] == "INV-0002"

    def test_create_invoice_due_date_before_issue_date(self, client, sample_invoice_data):
        """Test that due_date before issue_date returns 422 validation error."""
        sample_invoice_data["issue_date"] = "2026-03-08"
        sample_invoice_data["due_date"] = "2026-02-08"  # Before issue date
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 422

    def test_create_invoice_due_date_same_as_issue_date(self, client, sample_invoice_data):
        """Test that due_date can be same as issue_date."""
        sample_invoice_data["issue_date"] = "2026-02-08"
        sample_invoice_data["due_date"] = "2026-02-08"  # Same as issue date
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201

    def test_create_invoice_address_max_length(self, client, sample_invoice_data):
        """Test that address exceeding max length returns validation error."""
        sample_invoice_data["address"] = "x" * 501  # Exceeds max_length=500
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 422


class TestListInvoices:
    """Tests for GET /invoices endpoint."""

    def test_list_invoices_empty(self, client):
        """Test listing invoices when none exist."""
        response = client.get("/invoices")
        
        assert response.status_code == 200
        data = response.json()
        assert data["invoices"] == []
        assert data["total_count"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_list_invoices_with_data(self, client, sample_invoice_data):
        """Test listing invoices returns correct summary data."""
        # Create an invoice first
        client.post("/invoices", json=sample_invoice_data)
        
        response = client.get("/invoices")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["invoices"]) == 1
        assert data["total_count"] == 1
        
        invoice = data["invoices"][0]
        assert invoice["invoice_no"] == "INV-0001"
        assert invoice["client_name"] == "Acme Corporation"
        assert invoice["item_count"] == 2
        assert invoice["tax"] == 350.0
        assert invoice["total"] == 3850.0

    def test_list_invoices_pagination(self, client, sample_invoice_data):
        """Test pagination works correctly."""
        # Create 5 invoices
        for _ in range(5):
            client.post("/invoices", json=sample_invoice_data)
        
        # Get first page
        response = client.get("/invoices?limit=2&offset=0")
        data = response.json()
        assert len(data["invoices"]) == 2
        assert data["total_count"] == 5
        assert data["invoices"][0]["invoice_no"] == "INV-0005"  # Most recent first
        assert data["invoices"][1]["invoice_no"] == "INV-0004"
        
        # Get second page
        response = client.get("/invoices?limit=2&offset=2")
        data = response.json()
        assert len(data["invoices"]) == 2
        assert data["invoices"][0]["invoice_no"] == "INV-0003"
        assert data["invoices"][1]["invoice_no"] == "INV-0002"

    def test_list_invoices_filter_by_client(self, client, sample_invoice_data):
        """Test filtering invoices by client_id."""
        # Create invoice for client 1
        client.post("/invoices", json=sample_invoice_data)
        
        # Create invoice for client 2
        sample_invoice_data["client_id"] = 2
        client.post("/invoices", json=sample_invoice_data)
        
        # Filter by client 1
        response = client.get("/invoices?client_id=1")
        data = response.json()
        assert len(data["invoices"]) == 1
        assert data["total_count"] == 1
        assert data["invoices"][0]["client_name"] == "Acme Corporation"

    def test_list_invoices_filter_by_issue_date(self, client, sample_invoice_data):
        """Test filtering invoices by issue date range."""
        # Create invoice with issue_date 2026-02-08
        client.post("/invoices", json=sample_invoice_data)
        
        # Create invoice with different issue_date
        sample_invoice_data["issue_date"] = "2026-01-15"
        sample_invoice_data["due_date"] = "2026-02-15"
        client.post("/invoices", json=sample_invoice_data)
        
        # Filter by issue_date_from
        response = client.get("/invoices?issue_date_from=2026-02-01")
        data = response.json()
        assert len(data["invoices"]) == 1
        assert data["invoices"][0]["issue_date"] == "2026-02-08"

    def test_list_invoices_filter_by_due_date(self, client, sample_invoice_data):
        """Test filtering invoices by due date range."""
        # Create invoice
        client.post("/invoices", json=sample_invoice_data)
        
        # Filter by due_date_to
        response = client.get("/invoices?due_date_to=2026-03-01")
        data = response.json()
        assert len(data["invoices"]) == 0  # due_date is 2026-03-08
        
        response = client.get("/invoices?due_date_to=2026-03-15")
        data = response.json()
        assert len(data["invoices"]) == 1


class TestGetInvoice:
    """Tests for GET /invoices/{id} endpoint."""

    def test_get_invoice_success(self, client, sample_invoice_data):
        """Test getting an invoice by ID."""
        # Create an invoice first
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        response = client.get(f"/invoices/{invoice_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invoice_id
        assert data["invoice_no"] == "INV-0001"
        assert data["subtotal"] == 3500.0
        assert data["tax"] == 350.0
        assert data["total"] == 3850.0
        assert len(data["items"]) == 2

    def test_get_invoice_not_found(self, client):
        """Test getting non-existent invoice returns 404."""
        response = client.get("/invoices/999")
        
        assert response.status_code == 404
        assert "Invoice not found" in response.json()["detail"]


class TestUpdateInvoice:
    """Tests for PUT /invoices/{id} endpoint."""

    def test_update_invoice_tax(self, client, sample_invoice_data):
        """Test updating invoice tax amount."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Update tax
        response = client.put(f"/invoices/{invoice_id}", json={"tax": 500.0})
        
        assert response.status_code == 200
        data = response.json()
        assert data["tax"] == 500.0
        assert data["subtotal"] == 3500.0  # Unchanged
        assert data["total"] == 4000.0  # 3500 + 500

    def test_update_invoice_client(self, client, sample_invoice_data):
        """Test updating invoice client."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Update client
        response = client.put(f"/invoices/{invoice_id}", json={"client_id": 2})
        
        assert response.status_code == 200
        data = response.json()
        assert data["client"]["id"] == 2
        assert data["client"]["name"] == "TechStart Inc."
        # Address should update to new client's address
        assert "Innovation Blvd" in data["address"]

    def test_update_invoice_custom_address(self, client, sample_invoice_data):
        """Test updating invoice with custom address."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Update address
        response = client.put(f"/invoices/{invoice_id}", json={"address": "New Address"})
        
        assert response.status_code == 200
        assert response.json()["address"] == "New Address"

    def test_update_invoice_dates(self, client, sample_invoice_data):
        """Test updating invoice dates."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Update dates
        response = client.put(f"/invoices/{invoice_id}", json={
            "issue_date": "2026-03-01",
            "due_date": "2026-04-01"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["issue_date"] == "2026-03-01"
        assert data["due_date"] == "2026-04-01"

    def test_update_invoice_items(self, client, sample_invoice_data):
        """Test updating invoice items replaces them completely."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Update items
        response = client.put(f"/invoices/{invoice_id}", json={
            "items": [{"product_id": 3, "quantity": 1}]  # Mobile App Development @ $3000
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == 3
        assert data["subtotal"] == 3000.0
        assert data["total"] == 3350.0  # 3000 + 350 tax

    def test_update_invoice_invalid_dates(self, client, sample_invoice_data):
        """Test that invalid date combination returns error."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Try to set due_date before issue_date (Pydantic returns 422 for validation errors)
        response = client.put(f"/invoices/{invoice_id}", json={
            "issue_date": "2026-03-01",
            "due_date": "2026-02-01"
        })
        
        assert response.status_code == 422

    def test_update_invoice_not_found(self, client):
        """Test updating non-existent invoice returns 404."""
        response = client.put("/invoices/999", json={"tax": 100})
        
        assert response.status_code == 404
        assert "Invoice not found" in response.json()["detail"]

    def test_update_invoice_invalid_client(self, client, sample_invoice_data):
        """Test updating with invalid client returns error."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Try to update with invalid client
        response = client.put(f"/invoices/{invoice_id}", json={"client_id": 999})
        
        assert response.status_code == 400
        assert "Client not found" in response.json()["detail"]

    def test_update_invoice_preserves_invoice_number(self, client, sample_invoice_data):
        """Test that update preserves the original invoice number."""
        # Create invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        original_invoice_no = create_response.json()["invoice_no"]
        
        # Update invoice
        response = client.put(f"/invoices/{invoice_id}", json={"tax": 500.0})
        
        assert response.status_code == 200
        assert response.json()["invoice_no"] == original_invoice_no


class TestDeleteInvoice:
    """Tests for DELETE /invoices/{id} endpoint."""

    def test_delete_invoice_success(self, client, sample_invoice_data):
        """Test successful invoice deletion."""
        # Create an invoice first
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/invoices/{invoice_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/invoices/{invoice_id}")
        assert get_response.status_code == 404

    def test_delete_invoice_not_found(self, client):
        """Test deleting non-existent invoice returns 404."""
        response = client.delete("/invoices/999")
        
        assert response.status_code == 404
        assert "Invoice not found" in response.json()["detail"]

    def test_delete_invoice_removes_items(self, client, sample_invoice_data):
        """Test that deleting invoice also removes its items (via CASCADE)."""
        # Create an invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Delete it
        client.delete(f"/invoices/{invoice_id}")
        
        # Verify invoice list is empty
        list_response = client.get("/invoices")
        assert list_response.json()["invoices"] == []
        assert list_response.json()["total_count"] == 0
