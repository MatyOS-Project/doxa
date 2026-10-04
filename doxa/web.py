"""Doxa's local web UI (zero dependencies, Python stdlib only).

Run ``doxa-ui`` and open http://localhost:8000 — pick two quantities and get the
verdict in three-valued logic, with a proof when the bound is provable.
"""
from __future__ import annotations

import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from doxa import __version__
from doxa import stoqos
from doxa import domains as D

_ASSETS = os.path.join(os.path.dirname(__file__), "assets")


def _asset(rel: str):
    rel = rel.split("?")[0]
    if ".." in rel or rel.startswith("/"):
        return None
    try:
        with open(os.path.join(_ASSETS, rel), "rb") as f:
            return f.read()
    except OSError:
        return None


_PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Doxa — Judge a statement</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<style>
:root{--bg:#fafafa;--surface:#fff;--ink:#0a0a0a;--muted:#6a6a6a;--line:#e4e4e4;--soft:#f0f0f0;--radius:12px;
--mono:'JetBrains Mono',ui-monospace,Menlo,monospace;
--sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
--display:'Fredoka','Inter',sans-serif;}
@media(prefers-color-scheme:dark){:root{--bg:#0b0b0c;--surface:#161617;--ink:#f4f4f5;
--muted:#9a9a9e;--line:#2a2a2c;--soft:#202022;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased;}
.stage{min-height:100vh;display:flex;justify-content:center;align-items:flex-start;padding:5vh 18px 48px;}
.panel{width:100%;max-width:600px;background:var(--surface);border:1px solid var(--line);
border-radius:18px;padding:30px 30px 22px;
box-shadow:0 1px 2px rgba(0,0,0,.05),0 20px 55px rgba(0,0,0,.12);}
.brandbar{display:flex;align-items:center;gap:14px;margin:0 0 20px;}
.mark{width:54px;height:54px;border-radius:14px;background:#fff;border:1px solid var(--line);
display:grid;place-items:center;flex:none;box-shadow:0 1px 2px rgba(0,0,0,.05);}
.mark img{width:40px;height:40px;}
.brandbar h1{font-family:var(--display);font-size:28px;font-weight:600;margin:0;letter-spacing:-.01em;}
.brandbar .tag2{font-size:13px;color:var(--muted);margin:2px 0 0;}
.sub{color:var(--muted);margin:0 0 22px;font-size:14px;}
.sub b{color:var(--ink);font-weight:600;font-family:var(--mono);font-size:13px;}
code{font-family:var(--mono);font-size:.92em;}
.card{background:none;border:0;border-radius:0;padding:0;box-shadow:none;margin-top:4px;}
label{display:block;font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:0 0 6px;}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:end;}
.grow{flex:1 1 260px;}
.build{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:6px;}
.q{flex:1 1 200px;min-width:150px;}
.le{font-family:var(--display);font-size:24px;color:var(--muted);flex:none;}
#domain{max-width:280px;}
.preview{margin-top:14px;padding:14px 16px;background:var(--bg);border:1px solid var(--line);
border-radius:10px;text-align:center;font-size:22px;min-height:26px;}
.preview .katex{color:var(--ink);}
.rclaim-tex{font-size:26px;margin:2px 0 4px;}
.rclaim-tex .katex{color:var(--ink);}
input,select{width:100%;padding:11px 12px;font-size:15px;border:1px solid var(--line);
border-radius:9px;background:var(--bg);color:var(--ink);font-family:var(--mono);}
input:focus,select:focus{outline:2px solid var(--ink);outline-offset:1px;border-color:var(--ink);}
button{padding:11px 22px;font-size:14px;font-weight:600;border:1px solid var(--ink);border-radius:9px;
background:var(--ink);color:var(--surface);cursor:pointer;font-family:var(--sans);}
button:hover{opacity:.88;}button:disabled{opacity:.5;cursor:default;}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0;}
.chip{font-size:12px;padding:4px 9px;border:1px solid var(--line);border-radius:7px;
background:var(--bg);color:var(--muted);cursor:pointer;font-family:var(--mono);}
.chip:hover{border-color:var(--ink);color:var(--ink);}
.hint{font-size:12px;color:var(--muted);margin:9px 0 0;}
.ex{margin:14px 0 0;font-size:13px;color:var(--muted);}
.ex a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line);margin-left:10px;cursor:pointer;}
.ex a:hover{border-color:var(--ink);}
.result{margin-top:22px;border-radius:var(--radius);padding:20px;border:1px solid var(--line);
border-left:4px solid var(--ink);display:none;background:var(--bg);}
.result.show{display:block;}
.claim{font-family:var(--mono);font-size:13px;color:var(--muted);}
.claim .dom{font-family:var(--sans);font-size:12px;color:var(--muted);margin-top:2px;}
.verdict{font-family:var(--display);font-size:30px;font-weight:600;letter-spacing:.01em;margin-top:8px;}
.t-unknown.result{border-left-color:var(--muted);}
.t-unknown .verdict{color:var(--muted);}
.rmeta{margin-top:10px;font-size:14px;color:var(--muted);}
.cert{margin-top:12px;padding:10px 12px;border:1px solid var(--line);border-radius:9px;
background:var(--soft);font-family:var(--mono);font-size:12.5px;color:var(--ink);}
.cert b{font-family:var(--sans);font-weight:600;letter-spacing:.04em;font-size:11px;
text-transform:uppercase;color:var(--muted);display:block;margin-bottom:4px;}
.bar{height:9px;border-radius:999px;background:var(--soft);margin-top:14px;overflow:hidden;border:1px solid var(--line);}
.bar>i{display:block;height:100%;background:var(--ink);}
.legend{margin-top:22px;padding-top:18px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);}
.legend b{color:var(--ink);font-weight:600;font-family:var(--mono);}
.legend div{margin-top:6px;padding-left:12px;border-left:2px solid var(--line);}
.err{color:var(--ink);font-size:14px;margin-top:14px;display:none;font-weight:600;}
.batch{margin-top:18px;border-top:1px solid var(--line);padding-top:14px;}
.batch summary{cursor:pointer;font-size:13px;color:var(--muted);font-weight:600;}
textarea{width:100%;margin-top:10px;padding:11px 12px;font:13px/1.5 var(--mono);
border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink);resize:vertical;}
#bout{margin-top:12px;}
.brow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:8px 11px;
border:1px solid var(--line);border-radius:9px;margin-top:6px;font-size:13px;font-family:var(--mono);background:var(--bg);}
.tag{font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:.05em;padding:2px 9px;border-radius:6px;
white-space:nowrap;border:1.5px solid var(--ink);}
.tag.true{background:var(--ink);color:var(--surface);}
.tag.false{background:var(--surface);color:var(--ink);}
.tag.realistic{background:var(--soft);color:var(--ink);border-color:var(--line);}
.tag.unknown{background:var(--surface);color:var(--muted);border-style:dashed;border-color:var(--muted);}
.foot{margin-top:16px;font-size:11.5px;color:var(--muted);}
.foot a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line);}
</style></head><body><div class="stage"><main class="panel">
<div class="brandbar"><span class="mark"><img src="/assets/stoqos.svg" alt="Doxa"></span>
  <div><h1>Doxa</h1><p class="tag2">a calibrated judge for the REALISTIC level</p></div></div>
<p class="sub">Pick two quantities. Doxa tells you if <b>A &le; B</b> is
<b>TRUE</b>, <b>FALSE</b>, or <b>REALISTIC</b> (looks right, but unproven).</p>
<div class="card">
  <label for="domain">Area of math</label>
  <select id="domain"></select>
  <label style="margin-top:16px">Is this always true?</label>
  <div class="build">
    <select id="lhs" class="q"></select>
    <span class="le">&le;</span>
    <select id="rhs" class="q"></select>
    <button id="go">Judge</button>
  </div>
  <div class="preview" id="preview"></div>
  <p class="ex">Try:
    <a data-l="radius" data-r="diameter" data-d="graphs">radius &le; diameter</a>
    <a data-l="diameter" data-r="radius" data-d="graphs">diameter &le; radius</a>
    <a data-l="tworadius" data-r="circumradius" data-d="triangles">Euler: 2r &le; R</a>
    <a data-l="next_prime" data-r="twice_prime" data-d="primes">Bertrand: p&#8345;&#8330;&#8321; &le; 2p&#8345;</a>
    <a data-l="geomean" data-r="mean" data-d="means">AM&ndash;GM: GM &le; AM</a>
  </p>
  <div class="err" id="err"></div>
  <div class="result" id="result">
    <div class="claim" id="rclaim"></div>
    <div class="verdict" id="rverdict"></div>
    <div class="rmeta" id="rnote"></div>
    <div class="cert" id="rcert" style="display:none"></div>
    <div class="bar" id="rbar" style="display:none"><i id="rbari"></i></div>
  </div>
  <details class="batch"><summary>Judge many at once</summary>
    <textarea id="blines" rows="4" spellcheck="false" placeholder="one claim per line, e.g.
radius <= diameter
girth <= diameter"></textarea>
    <div style="margin-top:8px"><button id="bgo">Judge all</button>
      <span class="hint" style="margin-left:8px">uses the domain selected above</span></div>
    <div id="bout"></div>
  </details>
</div>
<div class="legend">
  <div><b>TRUE</b> &mdash; proven, with a certificate or a known theorem. Only a proof asserts TRUE, never the score.</div>
  <div><b>FALSE</b> &mdash; a counterexample exists in the evidence.</div>
  <div><b>REALISTIC</b> &mdash; holds on the evidence but unproven; carries Doxa's calibrated probability.</div>
  <div><b>UNKNOWN</b> &mdash; cannot be judged (out of domain or unparseable).</div>
</div>
<p class="foot">MatyOS {{VERSION}} &middot; Doxa scores the middle; the kernel owns TRUE &middot;
<a href="https://github.com/MatyOS-Project/MatyOS">MatyOS</a> &middot; <span id="corpus">0</span> submissions collected</p>
<script>
const $=s=>document.querySelector(s);
let DOMS={};
const LINE={true:"✓ TRUE",false:"✗ FALSE",realistic:"◐ REALISTIC",unknown:"? UNKNOWN"};
// code name -> LaTeX (real math notation)
const LT={
 order:"n",size:"m",max_degree:"\\Delta",min_degree:"\\delta",avg_degree:"\\bar d",
 triangles:"t_\\triangle",diameter:"\\operatorname{diam}",radius:"\\operatorname{rad}",
 independence_number:"\\alpha",clique_number:"\\omega",chromatic_number:"\\chi",
 vertex_cover_number:"\\tau",domination_number:"\\gamma",matching_number:"\\nu",
 vertex_connectivity:"\\kappa",edge_connectivity:"\\lambda",degeneracy:"\\operatorname{deg}^{*}",
 girth:"g",average_eccentricity:"\\bar\\varepsilon",average_distance:"\\bar d_G",
 total_domination_number:"\\gamma_t",edge_cover_number:"\\rho",
 perimeter:"P",semiperim:"s",area:"[\\triangle]",inradius:"r",circumradius:"R",
 tworadius:"2r",longest:"c_{\\max}",shortest:"c_{\\min}",midside:"c_{\\mathrm{mid}}",height_long:"h_{\\max}",
 vmin:"\\min",harmean:"H",geomean:"G",mean:"A",rms:"Q",vmax:"\\max",median:"\\tilde x",
 twicemin:"2\\min",halfmax:"\\tfrac12\\max",vrange:"\\max-\\min",
 n:"n",d:"d(n)",sigma:"\\sigma(n)",phi:"\\varphi(n)",omega:"\\omega(n)",bigomega:"\\Omega(n)",
 isqrt:"\\lfloor\\sqrt n\\rfloor",twiceomega:"2\\omega(n)",halfsigma:"\\tfrac12\\sigma(n)",
 val:"a_n",idx:"n",idx2:"n^2",prefmax:"\\max_{k\\le n}a_k",prefsum:"\\textstyle\\sum_{k\\le n}a_k",
 prefmean:"\\bar a_n",double:"2a_n",
 prime:"p_n",next_prime:"p_{n+1}",twice_prime:"2p_n",gap:"g_n",nlogn:"n\\ln n",
 half_prime:"\\tfrac12 p_n",isqrt_prime:"\\lfloor\\sqrt{p_n}\\rfloor"};
const lat=n=>LT[n]||("\\text{"+n.replace(/_/g," ")+"}");
const lbl=n=>n.replace(/_/g," ");
function tex(latex,el,big){try{katex.render(latex,el,{throwOnError:false,displayMode:!!big});}
  catch(e){el.textContent=latex;}}
function renderPreview(){
  const l=$("#lhs").value,r=$("#rhs").value;
  if(l&&r) tex(lat(l)+" \\;\\le\\; "+lat(r),$("#preview"));
}
function opts(sel,names,pick){
  sel.innerHTML="";
  names.forEach(n=>{const o=document.createElement("option");o.value=n;o.textContent=lbl(n);sel.appendChild(o);});
  if(pick && names.includes(pick)) sel.value=pick;
}
async function loadDomains(){
  try{const r=await fetch("/api/domains");DOMS=(await r.json()).domains||{};}
  catch(e){DOMS={graphs:[]};}
  opts($("#domain"),Object.keys(DOMS),"graphs");
  if(!$("#domain").value) $("#domain").value=Object.keys(DOMS)[0];
  fillQuantities();
}
function fillQuantities(lpick,rpick){
  const names=DOMS[$("#domain").value]||[];
  opts($("#lhs"),names,lpick||names[0]);
  opts($("#rhs"),names,rpick||names[1]||names[0]);
  renderPreview();
}
async function judge(){
  const domain=$("#domain").value;
  const claim=$("#lhs").value+" <= "+$("#rhs").value;
  $("#err").style.display="none";$("#result").className="result";
  if($("#lhs").value===$("#rhs").value){showErr("pick two different quantities");return;}
  $("#go").disabled=true;$("#go").textContent="Judging…";
  try{
    const r=await fetch("/api/judge",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({claim,domain})});
    const j=await r.json();
    if(j.error){showErr(j.error);return;}
    show(j);
  }catch(e){showErr("could not reach the model: "+e);}
  finally{$("#go").disabled=false;$("#go").textContent="Judge";}
}
function showErr(m){$("#err").textContent=m;$("#err").style.display="block";}
function show(j){
  const t=j.truth;const res=$("#result");
  res.className="result show t-"+t;
  const parts=j.claim.split(" <= ");
  const rc=$("#rclaim"); rc.innerHTML='<div class="rclaim-tex"></div><div class="dom"></div>';
  tex((parts[1]?lat(parts[0])+" \\;\\le\\; "+lat(parts[1]):"\\text{"+j.claim+"}"),
      rc.querySelector(".rclaim-tex"),true);
  rc.querySelector(".dom").textContent=j.domain;
  $("#rverdict").textContent=LINE[t]||t.toUpperCase();
  $("#rnote").textContent=j.note||"";
  const cert=$("#rcert");
  if(j.certificate){cert.style.display="block";cert.innerHTML='<b>proof</b>'+esc(j.certificate);}
  else{cert.style.display="none";}
  const bar=$("#rbar");
  if(t==="realistic"&&typeof j.value==="number"){
    bar.style.display="block";$("#rbari").style.width=Math.round(j.value*100)+"%";
    $("#rnote").textContent="P(true) = "+j.value.toFixed(2)+
      "  (calibrated, confidence "+(j.confidence||0).toFixed(2)+") — "+(j.note||"");
  }else{bar.style.display="none";}
}
async function refreshCorpus(){
  try{const r=await fetch("/api/corpus");$("#corpus").textContent=(await r.json()).count;}catch(e){}
}
async function judgeAll(){
  const claims=$("#blines").value.split("\n").map(s=>s.trim()).filter(Boolean);
  const domain=$("#domain").value,out=$("#bout");
  if(!claims.length){out.innerHTML='<p class="hint">enter one claim per line</p>';return;}
  $("#bgo").disabled=true;$("#bgo").textContent="Judging…";
  try{
    const r=await fetch("/api/judge_batch",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({claims,domain})});
    const j=await r.json();
    if(j.error){out.innerHTML='<p class="hint">'+j.error+'</p>';return;}
    out.innerHTML=j.results.map(x=>{
      const v=(x.truth==="realistic"&&typeof x.value==="number")?(" "+x.value.toFixed(2)):"";
      return '<div class="brow"><span>'+esc(x.claim)+'</span>'+
             '<span class="tag '+x.truth+'">'+(LINE[x.truth]||x.truth)+v+'</span></div>';}).join("");
    refreshCorpus();
  }catch(e){out.innerHTML='<p class="hint">error: '+e+'</p>';}
  finally{$("#bgo").disabled=false;$("#bgo").textContent="Judge all";}
}
function esc(s){return s.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
$("#go").onclick=()=>{judge().then(refreshCorpus);};
$("#domain").addEventListener("change",()=>fillQuantities());
$("#lhs").addEventListener("change",renderPreview);
$("#rhs").addEventListener("change",renderPreview);
$("#bgo").onclick=judgeAll;
document.querySelectorAll(".ex a").forEach(a=>a.onclick=()=>{
  $("#domain").value=a.dataset.d;fillQuantities(a.dataset.l,a.dataset.r);$("#go").click();});
loadDomains();refreshCorpus();
</script></main></div></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        p = self.path
        if p in ("/", "/doxa", "/stoqos") or p.startswith(("/doxa?", "/stoqos?")):
            return self._send(200, _PAGE.replace("{{VERSION}}", __version__),
                              "text/html; charset=utf-8")
        if p.startswith("/assets/"):
            data = _asset(p[len("/assets/"):])
            ct = "image/svg+xml" if p.endswith(".svg") else "image/png"
            return self._send(200 if data else 404, data or b"", ct)
        if p == "/api/domains":
            out = {d.name: list(d.functionals.keys()) for d in D.all_domains()}
            return self._send(200, json.dumps({"domains": out}))
        if p == "/api/corpus":
            return self._send(200, json.dumps({"count": stoqos.corpus_size()}))
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        try:
            if self.path == "/api/judge":
                pl = self._body()
                claim = (pl.get("claim") or "").strip()
                domain = (pl.get("domain") or "graphs").strip()
                if not claim:
                    return self._send(200, json.dumps({"error": "enter a claim like:  radius <= diameter"}))
                if domain and domain != "graphs":
                    doms = {d.name: d for d in D.all_domains()}
                    if domain not in doms:
                        return self._send(200, json.dumps({"error": f"unknown domain '{domain}'"}))
                    j = stoqos.judge_domain(doms[domain], claim)
                else:
                    j = stoqos.judge(claim)
                stoqos.record_submission(claim, domain, j)
                return self._send(200, json.dumps({
                    "claim": claim, "domain": domain, "truth": stoqos.truth3(j),
                    "verdict": j.verdict, "value": j.value, "confidence": j.confidence,
                    "known": j.known, "note": j.note, "certificate": j.certificate}))
            if self.path == "/api/judge_batch":
                pl = self._body()
                claims = [str(c).strip() for c in (pl.get("claims") or []) if str(c).strip()]
                domain = (pl.get("domain") or "graphs").strip()
                if not claims:
                    return self._send(200, json.dumps({"error": "give a list of claims"}))
                dom = None if domain == "graphs" else domain
                out = []
                for c, j in zip(claims, stoqos.judge_many(claims, domain=dom)):
                    stoqos.record_submission(c, domain, j)
                    out.append({"claim": c, "truth": stoqos.truth3(j),
                                "value": j.value, "note": j.note})
                return self._send(200, json.dumps({"results": out, "domain": domain}))
            return self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:
            return self._send(200, json.dumps({"error": str(e)}))


def serve(port: int = 8000, host: str = "127.0.0.1") -> None:
    httpd = ThreadingHTTPServer((host, port), _Handler)
    url = f"http://{host}:{port}/doxa"
    print(f"Doxa {__version__} — {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    httpd.serve_forever()


def main() -> None:
    import sys
    port = 8000
    for a in sys.argv[1:]:
        if a.isdigit():
            port = int(a)
    serve(port=port)


if __name__ == "__main__":
    main()
