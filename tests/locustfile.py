import random
import string

from locust import HttpUser, between, task


class LinkShortenerUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.username = "user_" + "".join(random.choices(string.ascii_letters, k=8))
        self.password = "secret123"
        self.client.post("/signup", json={"username": self.username, "password": self.password})
        response = self.client.post(
            "/login", json={"username": self.username, "password": self.password}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None
        self.test_alias = f"alias_{self.username}"
        if self.token:
            self.client.post(
                "/links/shorten",
                json={"url": "https://google.com", "alias": self.test_alias},
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(3)
    def redirect_test(self):
        with self.client.get(
            f"/{self.test_alias}",
            catch_response=True,
            allow_redirects=False
        ) as response:
            if response.status_code == 307:
                response.success()

    @task(1)
    def shorten_new_link(self):
        if self.token:
            self.client.post(
                "/links/shorten",
                json={"url": "https://example.com/page/" + str(random.randint(1, 10000))},
                headers={"Authorization": f"Bearer {self.token}"}
            )
