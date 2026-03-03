import v2ray2proxy
import urllib.parse
import logging

class V2RayProxy(v2ray2proxy.V2RayProxy):
    def _parse_vless_link(self, link: str) -> dict:
        if not link.startswith("vless://"):
            raise ValueError("Not a valid VLESS link")

        try:
            parsed_url = urllib.parse.urlparse(link)

            if "@" not in parsed_url.netloc:
                raise ValueError("Invalid VLESS link: missing user info")
            user_info, host_port = parsed_url.netloc.split("@", 1)

            # Extract host and port
            if ":" not in host_port:
                raise ValueError("Inval..id VLESS link: missing port")
            host, port = host_port.rsplit(":", 1)

            # Parse query parameters
            params = dict(urllib.parse.parse_qsl(parsed_url.query))

            # Create outbound configuration
            outbound = {
                "protocol": "vless",
                "settings": {
                    "vnext": [{"address": host, "port": int(port), "users": [{"id": user_info, "encryption": params.get("encryption", "none"), "flow": params.get("flow", ""), "level": 0}]}]
                },
                "streamSettings": {"network": params.get("type", "tcp"), "security": params.get("security", "none")},
            }

            if params.get("security") == "tls":
                outbound["streamSettings"]["tlsSettings"] = {"serverName": params.get("sni", host)}

            # Handle WebSocket settings
            if params.get("type") == "ws":
                outbound["streamSettings"]["wsSettings"] = {"path": params.get("path", "/"), "headers": {"Host": params.get("host", host)}}

            if params.get("security") == "reality":
                outbound["streamSettings"]["realitySettings"] = {
                    "show": False,
                    "fingerprint": params.get("fp", params.get("fingerprint", "chrome")),
                    "serverName": params.get("sni", ""),
                    "publicKey": params.get("pbk", params.get("publicKey", "")),
                    "shortId": params.get("sid", params.get("shortId", "")),
                    "spiderX": ""
                }

            return outbound
        except Exception as e:
            logging.error(f"Failed to parse VLESS link: {str(e)}")
            raise ValueError(f"Invalid VLESS format: {str(e)}")