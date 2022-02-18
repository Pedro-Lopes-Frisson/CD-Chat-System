from src.server import Server

if __name__ == "__main__":
    s = Server()

    try:
        s.loop()
    except KeyboardInterrupt as e:
        s.close_server()
        print("Server closed by User input")
