import eventlet

eventlet.monkey_patch()

from app import create_app

app = create_app()

if __name__ == "__main__":
    from app.extensions import socket_io

    socket_io.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=True)
