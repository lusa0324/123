from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time, math

# --- 啟動並打開頁面 ---
options = webdriver.ChromeOptions()
# 明確指定 chromedriver 的路徑，這比相對路徑更穩定
svc = Service("/Users/qa-1/Downloads/chromedriver-mac-arm64/chromedriver")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=svc, options=options)
driver.get(
    "https://osmpc-c.bewen.me/"
    "?token=da7ebb611b280c80a0931c14397bc4d1-199469"
    "&platform=pc&mode=live&language=zh_cn"
    "&studioid=cp&gameid=osmjjbxgrand"
    "&lang=en_us&username=cposm002&device=pc"
)

# --- 更可靠的等待加載機制 ---
# 不再只是單純的 time.sleep()
# 使用 WebDriverWait 精確等待 Cocos Creator 遊戲引擎完全初始化
wait = WebDriverWait(driver, 30)
wait.until(lambda d: d.execute_script("return typeof cc !== 'undefined';")) # 等待 cc 物件定義
wait.until(lambda d: d.execute_script("return cc.director.getScene() !== null;")) # 等待場景加載
wait.until(lambda d: d.execute_script("return !!cc.find('Canvas');")) # 等待 Canvas 節點存在
time.sleep(5) # 額外等待一下，確保渲染穩定

# --- 實用的調試功能：打印當前所有 Label.string ---
# 這能幫助您快速了解當前界面上的文本內容，方便定位元素
all_labels = driver.execute_script("""
  var c = cc.find('Canvas');
  if (!c) return [];
  return c.getComponentsInChildren(cc.Label)
          .map(l=>l.string.trim())
          .filter(s=>s);
""")
print("🔍 當前場景裡的 Labels:", all_labels)

# --- 新增功能：滾動到指定 Label ---
def scroll_to_label(label_text: str):
    """在遊戲的 ScrollView 裡滾動到包含 label_text 的那一行"""
    js = f"""
    return (function(){{
      // 1) 拿到 Canvas 下指定路徑的 ScrollView 組件
      var scrollViewNode = cc.find('Canvas/lobby-rect/hall/gm-list/ScrollView-gms');
      if (!scrollViewNode) {{
        console.warn("ScrollView node not found at path: Canvas/lobby-rect/hall/gm-list/ScrollView-gms");
        return false;
      }}
      var sv = scrollViewNode.getComponent(cc.ScrollView);
      if (!sv) {{
        console.warn("ScrollView component not found on node.");
        return false;
      }}

      var view = sv.node.getChildByName('view');
      var content = view && view.getChildByName('content');
      if (!view || !content) {{
        console.warn("ScrollView view or content node not found.");
        return false;
      }}
      var viewWorldY = view.getWorldPosition().y;

      // 3) 找到目標行的世界 Y，並滾動
      var labels = cc.find('Canvas').getComponentsInChildren(cc.Label);
      for (var i=0; i<labels.length; i++) {{
        var lbl = labels[i];
        if (lbl.string.trim() === '{label_text}') {{
          // 獲取 Label 父節點的世界座標，因為它通常是可點擊的整行或按鈕
          var machineY = lbl.node.parent.getWorldPosition().y;
          var deltaY   = viewWorldY - machineY;
          // 調整 content 的 Y 座標來實現滾動
          content.setPosition(content.position.x,
                               content.position.y + deltaY);
          return true;
        }}
      }}
      console.warn("Label '{label_text}' not found in scene.");
      return false;
    })();
    """
    ok = driver.execute_script(js)
    if not ok:
        raise RuntimeError(f"滾動失敗：Label='{label_text}' 不存在，或找不到 ScrollView 或其內部節點")
    time.sleep(0.6) # 滾動後給予一些時間讓界面穩定

# --- 優化點擊功能 (`click_by_label`) ---
def click_by_label(label_text: str):
    """在 <canvas> 上 dispatch 鼠標事件點擊指定 label (其父節點)"""
    # 點擊前再次確認標籤存在，增加健壯性
    exists = driver.execute_script(f"""
      return cc.find('Canvas').getComponentsInChildren(cc.Label)
               .some(l=>l.string.trim()==='{label_text}');
    """)
    if not exists:
        raise RuntimeError(f"點擊失敗：場景中找不到 Label='{label_text}'")

    click_js = f"""
    return (function(){{
      var labels = cc.find('Canvas').getComponentsInChildren(cc.Label);
      var wp;
      for (var i=0; i<labels.length; i++) {{
        if (labels[i].string.trim() === '{label_text}') {{
          // 獲取 Label 父節點的世界座標進行點擊，通常更合理
          wp = labels[i].node.parent.getWorldPosition();
          break;
        }}
      }}
      if (!wp) {{
        console.warn("Could not find world position for Label '{label_text}'.");
        return false;
      }}

      var canvas = document.querySelector('canvas');
      var rect   = canvas.getBoundingClientRect();
      // 計算 Canvas 元素在瀏覽器中的縮放比例
      var scaleX = rect.width  / canvas.width;
      var scaleY = rect.height / canvas.height;

      // 將 Cocos Creator 的世界座標轉換為 Canvas 元素的本地座標，再轉換為瀏覽器客戶端座標
      var localX = canvas.width  / 2 + wp.x;
      var localY = canvas.height / 2 - wp.y; // Y 軸在 Cocos Creator 中是向上為正，在瀏覽器中是向下為正
      var cx = rect.left + localX * scaleX;
      var cy = rect.top  + localY * scaleY;

      // 在 Canvas 元素上觸發鼠標事件
      ['mousedown','mouseup','click'].forEach(function(evtName){{
        var evt = new MouseEvent(evtName, {{
          clientX: cx, clientY: cy,
          bubbles: true, cancelable: true, view: window
        }});
        canvas.dispatchEvent(evt);
      }});

      return true;
    }})();
    """
    ok = driver.execute_script(click_js)
    if not ok:
        raise RuntimeError(f"點擊失敗：dispatch 鼠標事件出錯或找不到目標座標")
    time.sleep(1) # 點擊後給予一些時間讓遊戲響應

# --- 主流程 ---
target = "Purple Celebration-NCH17"
print(f"嘗試滾動並點擊: {target}")
scroll_to_label(target)
click_by_label(target)

print("操作完成，瀏覽器保持打開，按回車退出。")
input()
# driver.quit()
