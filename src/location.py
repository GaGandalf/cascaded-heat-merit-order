class Location:
    def __init__(self, name: str, latitude: float, longitude: float):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return f"{self.name} at {self.latitude}, {self.longitude}"