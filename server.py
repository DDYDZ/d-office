"""D事务所统一服务器 — 静态文件 + 占星API"""
import sys,os,json,http.server
sys.path.insert(0,'/workspace/skills/vedic-astrology/scripts')
from timezonefinder import TimezoneFinder
from engine import calculate_full_chart
tf = TimezoneFinder()

CITY_COORDS = {
    "北京":(39.9042,116.4074),"上海":(31.2304,121.4737),"广州":(23.1291,113.2644),
    "深圳":(22.5431,114.0579),"杭州":(30.2741,120.1551),"南京":(32.0603,118.7969),
    "成都":(30.5728,104.0668),"重庆":(29.4316,106.9123),"武汉":(30.5928,114.3055),
    "西安":(34.3416,108.9398),"天津":(39.3434,117.3616),"苏州":(31.299,120.5853),
    "长沙":(28.2282,112.9388),"郑州":(34.7466,113.6254),"青岛":(36.0671,120.3826),
    "大连":(38.914,121.6147),"厦门":(24.4798,118.0894),"福州":(26.0745,119.2965),
    "昆明":(25.0389,102.7183),"贵阳":(26.647,106.6302),"沈阳":(41.8057,123.4315),
    "哈尔滨":(45.8038,126.535),"济南":(36.6512,117.1201),"合肥":(31.8206,117.2272),
    "南昌":(28.682,115.8579),"台北":(25.033,121.5654),"香港":(22.3193,114.1694),
    "澳门":(22.1987,113.5439),"拉萨":(29.65,91.1),"三亚":(18.2528,109.512),
    "桂林":(25.2736,110.29),"东京":(35.6762,139.6503),"首尔":(37.5665,126.978),
    "曼谷":(13.7563,100.5018),"新加坡":(1.3521,103.8198),"伦敦":(51.5074,-0.1278),
    "巴黎":(48.8566,2.3522),"纽约":(40.7128,-74.006),"洛杉矶":(34.0522,-118.2437),
    "悉尼":(-33.8688,151.2093),"墨尔本":(-37.8136,144.9631),"迪拜":(25.2048,55.2708),
    "孟买":(19.076,72.8777),"新德里":(28.6139,77.209),"罗马":(41.9028,12.4964),
    "米兰":(45.4642,9.19),"柏林":(52.52,13.405),"温哥华":(49.2827,-123.1207),
    "多伦多":(43.6532,-79.3832),"旧金山":(37.7749,-122.4194),
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=base_dir, **kwargs)

    def do_POST(self):
        if self.path == '/api/chart':
            cl = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(cl))
            try:
                y,m,d = map(int, body['birth_date'].split('-'))
                hh,mm = map(int, body['birth_time'].split(':'))
                place = body.get('birth_place','').strip()
                coords = None
                for city, c in CITY_COORDS.items():
                    if city in place or place in city: coords = c; break
                if not coords:
                    for city, c in CITY_COORDS.items():
                        if any(ch in city for ch in place[:2]): coords = c; break
                if not coords:
                    self.send_json(400, {"success":False,"error":f"未找到'{place}'"})
                    return
                lat, lon = coords
                tz_str = tf.timezone_at(lat=lat, lng=lon) or "Asia/Shanghai"
                chart = calculate_full_chart(y, m, d, hh, mm, lat, lon, tz_str)

                lagna = chart.get('lagna',{})
                planets = chart.get('planets',{})
                lines = [f"🌟 {body.get('name','匿名')} 的本命盘",
                    f"📍 {place} | 🕐 {body['birth_date']} {body['birth_time']}",
                    f"", f"上升: {lagna.get('sign','?')} {lagna.get('deg_str','')}", f"", "行星位置:"]
                for n in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
                    p = planets.get(n,{})
                    r = ' ℞' if p.get('retrograde') else ''
                    lines.append(f"  {n}: {p.get('sign','?')} {p.get('deg_str','')} 第{p.get('house','?')}宫{r}")
                cur = [d for d in chart.get('dashas',[]) if d.get('is_current')]
                if cur: lines.extend(["", f"当前大运: {cur[0].get('planet','?')} ({cur[0].get('start','')}~{cur[0].get('end','')})"])
                sav = chart.get('sav_by_house',{})
                sv = [f"{h}宫:{sav.get(h,{}).get('value','?')}" for h in range(1,13)]
                lines.extend(["", f"SAV: {', '.join(sv)}"])
                self.send_json(200, {"success":True, "summary":"\n".join(lines)})
            except Exception as e:
                self.send_json(500, {"success":False, "error":str(e)})
        elif self.path == '/api/data/save':
            cl = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(cl))
            try:
                data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
                with open(data_file, 'w') as f:
                    json.dump(body, f, ensure_ascii=False)
                self.send_json(200, {"ok":True})
            except Exception as e:
                self.send_json(500, {"ok":False, "error":str(e)})
        else:
            self.send_json(404, {"error":"not found"})

    def do_GET(self):
        if self.path == '/api/data/load':
            try:
                data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
                if os.path.exists(data_file):
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    self.send_json(200, data)
                else:
                    self.send_json(200, {})
            except Exception as e:
                self.send_json(500, {"error":str(e)})
        else:
            super().do_GET()

    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

if __name__ == '__main__':
    import socketserver
    with socketserver.TCPServer(("0.0.0.0", 8000), Handler) as httpd:
        print("🏛️ D事务所统一服务启动: http://0.0.0.0:8000")
        httpd.serve_forever()
