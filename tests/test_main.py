from http import client


def test_create_user():
      response = client.post("/users/", json={"username": "testuser", "password": "testpass"})
      assert response.status_code == 200
      assert response.json()["username"] == "testuser"