from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time, math

# —— 启动并打开页面 —— #
options = webdriver.ChromeOptions()
svc = Service("/Users/qa-1/Downloads/chromedriver-mac-arm64/chromedriver")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=svc, options=options)
driver.get(
    "https://osmclient-c.bewen.me/?token=2f55eccbb7d46e9c2cbe16d210d0a6f5-321858&platform=pc&mode=live&language=zh_cn&studioid=cp&gameid=osmlionsreward&lang=en_us&username=cplusa06&device=pc"
)

# 等待加载
time.sleep(15)
wait = WebDriverWait(driver, 30)
wait.until(lambda d: d.execute_script("return typeof cc !== 'undefined';"))
wait.until(lambda d: d.execute_script("return cc.director.getScene() !== null;"))
wait.until(lambda d: d.execute_script("return !!cc.find('Canvas');"))

# 滚动到列表底部，确保所有节点 attach
scroll_js = """
(function(){
  var sv = cc.find('Canvas/lobby-rect/hall/gm-list/ScrollView-gms')
            .getComponent(cc.ScrollView);
  if (!sv) return false;
  sv.scrollToBottom(1.5);
  return true;
})();
"""
driver.execute_script(scroll_js)
time.sleep(1)

# 调试：打印当前所有 Label.string
all_labels = driver.execute_script("""
  var c = cc.find('Canvas');
  if (!c) return [];
  return c.getComponentsInChildren(cc.Label)
          .map(l=>l.string.trim())
          .filter(s=>s);
""")
print("🔍 当前场景里的 Labels:", all_labels)
time.sleep(1)

# 找到指定遊戲
def scroll_to_label(label_text: str, duration: float = 1):
    """
    把 ScrollView-gms 下，文字等于 label_text 的那一项平滑滚动到视口正中间。
    duration 是动画时长（秒）。
    """
    js = f"""
    return (function(){{
      // 1) 拿到所有 ScrollView，并优先选名字叫 ScrollView-gms 的
      var scrolls = cc.find('Canvas').getComponentsInChildren(cc.ScrollView);
      if (!scrolls || scrolls.length === 0) return false;
      var sv = scrolls.find(s=>s.node.name==='ScrollView-gms') || scrolls[0];
      var view    = sv.node.getChildByName('view');
      var content = view && view.getChildByName('content');
      if (!view || !content) return false;

      // 2) 取视口中心的世界 Y
      var viewWorldY = view.getWorldPosition().y;

      // 3) 找到那一行对应的 machine_item 世界 Y
      var labels = cc.find('Canvas').getComponentsInChildren(cc.Label);
      for (var i = 0; i < labels.length; i++) {{
        if (labels[i].string.trim() === '{label_text}') {{
          var machine = labels[i].node.parent;
          var machineY = machine.getWorldPosition().y;

          // 4) 计算 content 需要平移的本地偏移 deltaY
          var deltaY = viewWorldY - machineY;
          var fromPos = content.position.clone();
          var toPos   = cc.v3(fromPos.x, fromPos.y + deltaY, fromPos.z);

          // 5) 用 cc.tween 平滑过渡
          cc.tween(content)
            .to({duration}, {{ position: toPos }})
            .start();

          return true;
        }}
      }}
      return false;
    }})();
    """
    print(f"==> 滚到 “{label_text}” 并居中，动画时长 {duration}s")
    ok = driver.execute_script(js)
    print("滚动脚本执行结果：", ok)
    if not ok:
        raise RuntimeError(f"滚动失败：没有找到 Label='{label_text}' 或 ScrollView-gms")
    time.sleep(duration + 0.2)

# 進入指定遊戲
def hover_and_click_preview(label_text: str):
    """
    在 Cocos 场景里，找到指定 label_text 所在的 machine_item 下的 preview_img 节点，
    然后模拟鼠标移动到该位置（触发 normal_hover），再点击一次。
    """

    # 1) 先运行 JS，将世界坐标转换为引擎“屏幕坐标”（以画布左下角为原点，单位是引擎像素）
    coord_js = f"""
    return (function(){{
      // 获取场景中所有的 Label 组件
      var labels = cc.find('Canvas').getComponentsInChildren(cc.Label);
      for (var i = 0; i < labels.length; i++) {{
        // 找到文字匹配的那个 Label
        if (labels[i].string.trim() === '{label_text}') {{
          var preview = labels[i].node.parent.getChildByName('preview_img');
          if (!preview) return null;
          // 拿到它的世界坐标
          var wp = preview.getWorldPosition();

          // 找到 Canvas 下挂载的主摄像机节点 MainCamera
          var camNode = cc.find('Canvas/MainCamera')
                     || cc.find('Canvas').getComponentInChildren(cc.Camera).node;
          var cam = camNode.getComponent(cc.Camera);

          // 用摄像机把世界坐标转换成屏幕坐标 (Vec3)，z 分量可忽略
          var sp = cam.worldToScreen(wp, new cc.Vec3());
          return {{ x: sp.x, y: sp.y }};
        }}
      }}
      return null;
    }})();
    """
    sp = driver.execute_script(coord_js)
    if not sp:
        raise RuntimeError(f"找不到 '{label_text}' 对应的 preview_img 节点或摄像机")
    print(f"🎯 引擎屏幕坐标: x={sp['x']:.1f}, y={sp['y']:.1f}")

    # 2) 将引擎像素坐标转换为浏览器的 clientX/clientY
    canvas = driver.find_element(By.TAG_NAME, "canvas")
    rect   = canvas.rect  # 返回 {'x','y','width','height'} CSS 像素信息

    # 画布内部像素大小
    canvas_width  = int(canvas.get_attribute('width'))
    canvas_height = int(canvas.get_attribute('height'))

    # 计算在 CSS 像素下的坐标
    scaleX = rect['width']  / canvas_width
    scaleY = rect['height'] / canvas_height

    sx = sp['x'] * scaleX
    sy = sp['y'] * scaleY

    # clientX = 画布左上角 X + sx
    cx = rect['x'] + sx
    # clientY = 画布顶部 Y + (画布高度 - sy)
    cy = rect['y'] + rect['height'] - sy

    print(f"→ 转换后浏览器点击坐标: clientX={cx:.1f}, clientY={cy:.1f}")

    # 3) 派发原生鼠标事件：先 mousemove（触发 hover），再 click
    dispatch_js = f"""
    return (function(){{
      var c = document.querySelector('canvas');
      // 模拟鼠标移动（hover）
      c.dispatchEvent(new MouseEvent('mousemove', {{
        clientX: {cx}, clientY: {cy},
        bubbles: true, cancelable: true, view: window
      }}));
      // 模拟点击：mousedown, mouseup, click
      ['mousedown','mouseup','click'].forEach(function(evtName) {{
        c.dispatchEvent(new MouseEvent(evtName, {{
          clientX: {cx}, clientY: {cy},
          bubbles: true, cancelable: true, view: window
        }}));
      }});
      return true;
    }})();
    """
    ok = driver.execute_script(dispatch_js)
    print("hover+click 派发结果：", ok)
    if not ok:
        raise RuntimeError("hover+click 事件派发失败")
    time.sleep(1)

# 進入遊戲後點擊指定座標
def click_nth_p1_under_touch(p1_index: int, scroll_duration: float = 0.5):
    """
    定位到 Canvas/game-rect/game/gm_double/videoLayout/main/touch
    下面的第 p1_index 个 p1 节点，平滑滚动（如果需要），然后点击它。
    """
    # 1) 先拿到那个节点的 worldPosition
    wp = driver.execute_script(f"""
    return (function(){{
      // 直接找到 touch 容器
      var touchNode = cc.find(
        'Canvas/game-rect/game/gm_double/videoLayout/main/touch'
      );
      if (!touchNode) return null;
      var items = touchNode.children.filter(c => c.name === 'p1');
      var idx = {p1_index} - 1;
      if (items.length <= idx) return null;
      // 拿 worldPosition
      return items[idx].getWorldPosition();
    }})();
    """)
    if not wp:
        print(f"⚠️ 找不到 touch 下的第 {p1_index} 个 p1，跳过这一步")
        return False
    
    # 2) 如果需要滚动：把这个 worldPosition 滚到视口中央
    #    （如果这个层级本身不在 ScrollView 里，也可以跳过这步）
    driver.execute_script(f"""
    (function(){{
      var content = cc.find('Canvas/game-rect/game/gm_double/videoLayout/main/touch');
      if (!content) return false;
      // 视口中心 worldY
      var camNode = cc.find('Canvas/MainCamera') 
                 || cc.find('Canvas').getComponentInChildren(cc.Camera).node;
      var cam = camNode.getComponent(cc.Camera);
      // worldToScreen 用不到滚 content，通常 touch 是固定在屏幕上的
      // 如果需要在 touch 容器里滚动，就再拿父级做 tween
      return true;
    }})();
    """)
    # 如果有动画需要等待，可 time.sleep(scroll_duration)

    # 3) worldToScreen → engine 像素
    sp = driver.execute_script(f"""
    return (function(){{
      var camNode = cc.find('Canvas/MainCamera')
                 || cc.find('Canvas').getComponentInChildren(cc.Camera).node;
      var cam = camNode.getComponent(cc.Camera);
      var out = cam.worldToScreen(cc.v3({wp['x']}, {wp['y']}, 0), new cc.Vec3());
      return {{ x: out.x, y: out.y }};
    }})();
    """)
    if not sp:
        raise RuntimeError("worldToScreen 转换失败")

    # 4) engine 像素 → 浏览器 clientX/Y
    canvas = driver.find_element(By.TAG_NAME, "canvas")
    rect   = canvas.rect
    cw     = int(canvas.get_attribute('width'))
    ch     = int(canvas.get_attribute('height'))

    sx = sp['x'] * (rect['width']  / cw)
    sy = sp['y'] * (rect['height'] / ch)
    cx = rect['x'] + sx
    cy = rect['y'] + rect['height'] - sy

    # 5) 派发鼠标事件
    time.sleep(10)
    dispatch_js = f"""
    return (function(){{
      var c = document.querySelector('canvas');
      c.dispatchEvent(new MouseEvent('mousemove', {{clientX:{cx}, clientY:{cy}, bubbles:true}}));
      ['mousedown','mouseup','click'].forEach(evtName => {{
        c.dispatchEvent(new MouseEvent(evtName, {{
          clientX:{cx}, clientY:{cy}, bubbles:true
        }}));
      }});
      return true;
    }})();
    """
    ok = driver.execute_script(dispatch_js)
    print(f" {p1_index} 點擊結果：", ok)
    if not ok:
        raise RuntimeError(f"第 {p1_index} 个 p1 点击派发失败")
    time.sleep(0.5)

# 點
def click_play_key_once():
    """
    找到 Canvas/.../play-key 节点并 dispatch 点击事件一次。
    """
    # 1) 拿到 play-key 的 worldPosition
    wp = driver.execute_script("""
      return (function(){
        var node = cc.find(
          'Canvas/game-rect/game/Handle/handle5/play-key'
        );
        if (!node) return null;
        return node.getWorldPosition();
      })();
    """)
    if not wp:
        print("找不到 play-key 节点")
        return False


    # 2) worldToScreen → 引擎屏幕像素
    sp = driver.execute_script(f"""
      return (function(){{
        var camNode = cc.find('Canvas/MainCamera')
                   || cc.find('Canvas').getComponentInChildren(cc.Camera).node;
        var cam     = camNode.getComponent(cc.Camera);
        var out     = cam.worldToScreen(
          cc.v3({wp['x']}, {wp['y']}, 0),
          new cc.Vec3()
        );
        return {{ x: out.x, y: out.y }};
      }})();
    """)
    if not sp:
      print("worldToScreen 转换失败，跳过点击")
      return False


    # 3) 引擎像素 → 浏览器 clientX/Y
    canvas = driver.find_element(By.TAG_NAME, "canvas")
    rect   = canvas.rect
    cw     = int(canvas.get_attribute('width'))
    ch     = int(canvas.get_attribute('height'))

    sx = sp['x'] * (rect['width']  / cw)
    sy = sp['y'] * (rect['height'] / ch)
    cx = rect['x'] + sx
    cy = rect['y'] + rect['height'] - sy

    # 4) 派发原生鼠标事件
    dispatch_js = f"""
      return (function(){{
        var c = document.querySelector('canvas');
        // hover 有时能确保按钮进入可点击状态
        c.dispatchEvent(new MouseEvent('mousemove', {{
          clientX: {cx}, clientY: {cy}, bubbles: true
        }}));
        ['mousedown','mouseup','click'].forEach(function(evtName){{
          c.dispatchEvent(new MouseEvent(evtName, {{
            clientX: {cx}, clientY: {cy}, bubbles: true
          }}));
        }});
        return true;
      }})();
    """
    ok = driver.execute_script(dispatch_js)
    if not ok:
        raise RuntimeError("play-key 点击派发失败")

def click_play_key_loop(interval: float = 1):
    """
    无限循环点击 play-key，每次间隔 interval 秒。
    按 Ctrl+C 手动停止。
    """
    print(f"开始循环点击 play-key，每 {interval}s 点击一次，按 Ctrl+C 停止…")
    try:
        while True:
            click_play_key_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n已收到中断信号，停止循环。")

# —— 主流程 —— #
target = "Lucky 88 Extra Choice-NWR2132"
scroll_to_label(target)
hover_and_click_preview(target)
click_nth_p1_under_touch(1)
click_play_key_loop(interval=1)

print("操作完成，浏览器保持打开，按回车退出。")
input()
