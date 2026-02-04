"""
网络诊断测试脚本
测试为什么浏览器可以访问但Python无法访问东方财富API
"""
import os
import sys

def test_environment():
    """测试环境变量"""
    print("\n=== 1. 环境变量检查 ===")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
    for var in proxy_vars:
        value = os.environ.get(var, '未设置')
        if value != '未设置':
            print(f"  ⚠️ {var} = {value}")
        else:
            print(f"  ✓ {var} = {value}")

def test_dns():
    """测试DNS解析"""
    print("\n=== 2. DNS解析测试 ===")
    import socket
    hosts = ['82.push2.eastmoney.com', 'push2.eastmoney.com', 'quote.eastmoney.com']
    for host in hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"  ✓ {host} -> {ip}")
        except Exception as e:
            print(f"  ❌ {host} -> 解析失败: {e}")

def test_ssl():
    """测试SSL连接"""
    print("\n=== 3. SSL连接测试 ===")
    import ssl
    import socket
    
    context = ssl.create_default_context()
    print(f"  SSL版本: {ssl.OPENSSL_VERSION}")
    
    hosts = [('82.push2.eastmoney.com', 443), ('push2.eastmoney.com', 443)]
    for host, port in hosts:
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    print(f"  ✓ {host}:{port} SSL连接成功")
        except Exception as e:
            print(f"  ❌ {host}:{port} SSL连接失败: {e}")

def test_requests():
    """测试requests库"""
    print("\n=== 4. requests库测试 ===")
    try:
        import requests
        print(f"  requests版本: {requests.__version__}")
        
        url = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=3&po=1&np=1&fltt=2&fid=f3&fs=m:0+t:6&fields=f2,f3,f12,f14"
        
        # 不使用代理
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://quote.eastmoney.com/"
            },
            timeout=10,
            proxies={"http": None, "https": None},
            verify=True
        )
        print(f"  ✓ HTTP请求成功, 状态码: {response.status_code}")
        print(f"  响应长度: {len(response.text)} 字符")
        print(f"  响应预览: {response.text[:200]}...")
    except Exception as e:
        print(f"  ❌ requests请求失败: {e}")

def test_httpx():
    """测试httpx库"""
    print("\n=== 5. httpx库测试 ===")
    try:
        import httpx
        print(f"  httpx版本: {httpx.__version__}")
        
        url = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=3&po=1&np=1&fltt=2&fid=f3&fs=m:0+t:6&fields=f2,f3,f12,f14"
        
        with httpx.Client(timeout=10.0, verify=True, proxy=None) as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Referer": "https://quote.eastmoney.com/"
                }
            )
            print(f"  ✓ httpx请求成功, 状态码: {response.status_code}")
            print(f"  响应长度: {len(response.text)} 字符")
    except Exception as e:
        print(f"  ❌ httpx请求失败: {e}")

def test_akshare_one():
    """测试akshare-one"""
    print("\n=== 6. akshare-one测试 ===")
    try:
        from akshare_one import get_realtime_data
        print("  ✓ akshare_one导入成功")
        
        print("  正在获取单只股票数据...")
        df = get_realtime_data(symbol="600000")
        if df is not None and not df.empty:
            print(f"  ✓ 获取成功, 行数: {len(df)}")
            print(df.head())
        else:
            print("  ❌ 返回空数据")
    except Exception as e:
        print(f"  ❌ akshare-one测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_urllib():
    """测试最基础的urllib"""
    print("\n=== 7. urllib测试 ===")
    try:
        import urllib.request
        
        url = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=3&po=1&np=1&fltt=2&fid=f3&fs=m:0+t:6&fields=f2,f3,f12,f14"
        
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://quote.eastmoney.com/"
            }
        )
        
        # 不使用代理
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        
        with opener.open(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            print(f"  ✓ urllib请求成功, 状态码: {response.status}")
            print(f"  响应长度: {len(data)} 字符")
    except Exception as e:
        print(f"  ❌ urllib请求失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  网络诊断测试")
    print("=" * 60)
    
    test_environment()
    test_dns()
    test_ssl()
    test_urllib()
    test_requests()
    test_httpx()
    test_akshare_one()
    
    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)
