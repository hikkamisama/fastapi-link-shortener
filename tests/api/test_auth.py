def test_signup_success(client):
    response = client.post(
        "/signup",
        json={"username": "new_tester", "password": "strongpassword123"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "new_tester"
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()

def test_signup_duplicate_username(client):
    client.post("/signup", json={"username": "duplicate_me", "password": "password"})
    response = client.post("/signup", json={"username": "duplicate_me", "password": "password"})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success(client):
    client.post("/signup", json={"username": "loggy", "password": "secretpassword"})
    response = client.post("/login", json={"username": "loggy", "password": "secretpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failures(client):
    client.post("/signup", json={"username": "realuser", "password": "realpassword"})
    res1 = client.post("/login", json={"username": "fakeuser", "password": "realpassword"})
    assert res1.status_code == 401
    assert "Incorrect" in res1.json()["detail"]
    res2 = client.post("/login", json={"username": "realuser", "password": "wrongpassword"})
    assert res2.status_code == 401
    assert "Incorrect" in res2.json()["detail"]
