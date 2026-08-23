from scripts.keep_public import tunnel_connected


def test_tunnel_connected_uses_latest_register_not_an_old_error():
    text = (
        "ERR Serve tunnel error error=timeout\n"
        "INF Registered tunnel connection connIndex=0 protocol=http2\n"
    )
    assert tunnel_connected(text) is True


def test_tunnel_connected_false_after_drop():
    text = (
        "INF Registered tunnel connection connIndex=0 protocol=http2\n"
        "ERR failed to serve tunnel connection error=timeout\n"
    )
    assert tunnel_connected(text) is False


def test_tunnel_connected_false_before_register():
    assert tunnel_connected("Requesting new quick Tunnel") is False
