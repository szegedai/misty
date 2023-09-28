from mistyPy.Robot import Robot

class Misty(Robot):
    def __determine_ip(self, ip: str) -> None:
        self.ip = ip