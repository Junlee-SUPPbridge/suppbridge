#!/usr/bin/env bash
# Responsive / layout validation for the SuppBridge static site.
#
# Serves the repo over HTTP and drives a real Chromium through the required
# breakpoints, reporting horizontal overflow, broken images, dead SVG icon
# references, broken images and CTA visibility.
#
# Usage:  bash scripts/responsive-check.sh [port]
# Requires: agent-browser on PATH (see the agent-browser skill).

set -uo pipefail

PORT="${1:-8899}"
BASE="http://127.0.0.1:${PORT}"
VIEWPORTS=("375 812" "390 844" "414 896" "768 1024" "1024 768" "1440 900")
PAGES=(
  "/:index"
  "/china-supplement-sourcing.html:sourcing"
  "/product-formats.html:formats"
  "/thanks.html:thanks"
  "/blog/:blog-index"
  "/blog/verify-china-supplement-manufacturer.html:article"
  "/blog/how-to-develop-a-supplement-product-in-china.html:article-product"
)

# NOTE: body has overflow-x:hidden, which can clamp documentElement.scrollWidth
# and hide real overflow. So we ALSO walk every element and flag any that is
# wider than the viewport without a horizontally-scrollable ancestor.
DIAG='JSON.stringify({scrollW:document.documentElement.scrollWidth,innerW:window.innerWidth,overflow:document.documentElement.scrollWidth>window.innerWidth+1,containerMax:(function(){var c=document.querySelector(".container");return c?getComputedStyle(c).maxWidth:null})(),navToggle:(function(){var t=document.getElementById("navToggle");return t?getComputedStyle(t).display!=="none":null})(),navLinks:(function(){var l=document.querySelector(".nav-links");return l?getComputedStyle(l).display!=="none":null})(),h1:(function(){var h=document.querySelector("h1");return h?getComputedStyle(h).fontSize:null})(),bodyPadTop:getComputedStyle(document.body).paddingTop,brokenImgs:Array.from(document.images).filter(function(i){return i.complete&&i.naturalWidth===0}).map(function(i){return i.getAttribute("src")}),deadIcons:Array.from(document.querySelectorAll("svg use")).filter(function(u){var id=(u.getAttribute("href")||"").replace("#","");return !document.getElementById(id)}).length,icons:document.querySelectorAll("svg use").length,cta:(function(){var b=document.querySelector(".btn--primary");if(!b)return null;var r=b.getBoundingClientRect();return {t:b.textContent.trim().slice(0,34),w:Math.round(r.width),h:Math.round(r.height)}})(),wideEls:(function(){function scrollable(e){var n=e.parentElement;while(n&&n!==document.body){var ox=getComputedStyle(n).overflowX;if(ox==="auto"||ox==="scroll")return true;n=n.parentElement}return false}return Array.from(document.querySelectorAll("body *")).filter(function(e){return e.getBoundingClientRect().width>window.innerWidth+2&&!scrollable(e)}).slice(0,6).map(function(e){return e.tagName+"."+String(e.className).slice(0,30)})})()})'

fail=0

for entry in "${PAGES[@]}"; do
  path="${entry%%:*}"
  name="${entry##*:}"
  echo "══════════════════════════════════════════════════"
  echo "PAGE: ${path}"
  echo "══════════════════════════════════════════════════"
  agent-browser open "${BASE}${path}" >/dev/null 2>&1
  sleep 0.6

  for vp in "${VIEWPORTS[@]}"; do
    set -- $vp
    w="$1"; h="$2"
    agent-browser set viewport "$w" "$h" >/dev/null 2>&1
    sleep 0.35
    out="$(agent-browser eval "$DIAG" 2>/dev/null | tr -d '\n')"
    printf "  %5sx%-5s  %s\n" "$w" "$h" "$out"
    case "$out" in
      *'"overflow":true'*) echo "        !! HORIZONTAL OVERFLOW"; fail=1 ;;
    esac
    case "$out" in
      *'"brokenImgs":[]'*) : ;;
      *'"brokenImgs":['*) echo "        !! BROKEN IMAGE"; fail=1 ;;
    esac
    case "$out" in
      *'"deadIcons":0'*) : ;;
      *'"deadIcons":'*) echo "        !! DEAD SVG ICON REFERENCE"; fail=1 ;;
    esac
    case "$out" in
      *'"wideEls":[]'*) : ;;
      *'"wideEls":['*) echo "        !! ELEMENT WIDER THAN VIEWPORT (not scrollable)"; fail=1 ;;
    esac
  done
  echo ""
done

echo "══════════════════════════════════════════════════"
echo "Screenshots (375 / 768 / 1440)"
SHOT_DIR="${PWD}/.workbuddy/reports/shots"
mkdir -p "$SHOT_DIR"
for entry in "${PAGES[@]}"; do
  path="${entry%%:*}"
  name="${entry##*:}"
  agent-browser open "${BASE}${path}" >/dev/null 2>&1
  sleep 0.6
  for w in 375 768 1440; do
    agent-browser set viewport "$w" 900 >/dev/null 2>&1
    sleep 0.4
    agent-browser screenshot --full "$SHOT_DIR/${name}-${w}.png" >/dev/null 2>&1
  done
  echo "  + ${name} (375/768/1440) -> ${SHOT_DIR}"
done

agent-browser close --all >/dev/null 2>&1

echo ""
if [ "$fail" -eq 0 ]; then
  echo "RESULT: PASS — no overflow, no broken images, no dead icons."
else
  echo "RESULT: ISSUES FOUND (see !! lines above)."
fi
exit "$fail"
