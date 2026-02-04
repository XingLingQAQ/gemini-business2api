"""
Gemini自动化登录模块 - Steel 云端浏览器版本
使用 Playwright 连接 Steel 云端浏览器，完全复制 DrissionPage 版本的登录流程
"""
import os
import random
import string
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from core.base_task_service import TaskCancelledError


# 常量
AUTH_HOME_URL = "https://auth.business.gemini.google/"
DEFAULT_XSRF_TOKEN = "KdLRzKwwBTD5wo8nUollAbY6cW0"


class GeminiAutomationSteel:
    """Gemini自动化登录 - Steel 云端浏览器版本"""

    def __init__(
        self,
        steel_cdp_url: str,
        user_agent: str = "",
        timeout: int = 60,
        log_callback=None,
    ) -> None:
        self.steel_cdp_url = steel_cdp_url
        self.user_agent = user_agent or self._get_ua()
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        self.log_callback = log_callback
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def stop(self) -> None:
        """外部请求停止：尽力关闭浏览器实例"""
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass

    def login_and_extract(self, email: str, mail_client) -> dict:
        """执行登录并提取配置"""
        try:
            self._connect()
            return self._run_flow(self._page, email, mail_client)
        except TaskCancelledError:
            raise
        except Exception as exc:
            self._log("error", f"automation error: {exc}")
            return {"success": False, "error": str(exc)}
        finally:
            self.stop()

    def _connect(self) -> None:
        """连接到 Steel 云端浏览器"""
        try:
            self._log("info", "connecting to Steel cloud browser...")

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.connect_over_cdp(self.steel_cdp_url)

            # 获取或创建 context 和 page
            if self._browser.contexts:
                self._context = self._browser.contexts[0]
            else:
                self._context = self._browser.new_context()

            if self._context.pages:
                self._page = self._context.pages[0]
            else:
                self._page = self._context.new_page()

            # 设置默认超时
            self._page.set_default_timeout(self.timeout)

            # 反检测：注入脚本隐藏自动化特征
            try:
                self._page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                    window.chrome = {runtime: {}};

                    // 额外的反检测措施
                    Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 1});
                    Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                    Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});

                    // 隐藏 headless 特征
                    Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                    Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});

                    // 模拟真实的 permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({state: Notification.permission}) :
                            originalQuery(parameters)
                    );
                """)
            except Exception:
                pass

            self._log("info", "Steel cloud browser connected successfully")

        except ImportError:
            self._log("error", "Steel requires Playwright: pip install playwright && playwright install chromium")
            raise
        except Exception as e:
            self._log("error", f"failed to connect to Steel: {e}")
            raise

    def _run_flow(self, page: Page, email: str, mail_client) -> dict:
        """执行登录流程"""

        # 记录开始时间，用于邮件时间过滤
        send_time = datetime.now()

        # Step 1: 导航到首页并设置 Cookie
        self._log("info", f"opening login page: {email}")

        page.goto(AUTH_HOME_URL, wait_until="domcontentloaded", timeout=self.timeout)
        time.sleep(2)

        # 设置两个关键 Cookie
        try:
            self._log("info", "setting authentication Cookies...")
            page.context.add_cookies([
                {
                    "name": "__Host-AP_SignInXsrf",
                    "value": DEFAULT_XSRF_TOKEN,
                    "domain": "auth.business.gemini.google",
                    "path": "/",
                    "secure": True,
                },
                {
                    "name": "_GRECAPTCHA",
                    "value": "09ABCL...",
                    "domain": ".google.com",
                    "path": "/",
                    "secure": True,
                }
            ])
            self._log("info", "Cookies set successfully")
        except Exception as e:
            self._log("warning", f"failed to set Cookies: {e}")

        login_hint = quote(email, safe="")
        login_url = f"https://auth.business.gemini.google/login/email?continueUrl=https%3A%2F%2Fbusiness.gemini.google%2F&loginHint={login_hint}&xsrfToken={DEFAULT_XSRF_TOKEN}"
        self._log("info", "navigating to login URL...")
        try:
            page.goto(login_url, wait_until="domcontentloaded", timeout=self.timeout)
        except PlaywrightTimeoutError:
            self._log("warning", "page load timeout, but continuing (page may already be loaded)")
        time.sleep(5)

        # Step 2: 检查当前页面状态
        current_url = page.url
        self._log("info", f"current URL: {current_url}")
        has_business_params = "business.gemini.google" in current_url and "csesidx=" in current_url and "/cid/" in current_url

        if has_business_params:
            self._log("info", "already logged in, extracting config directly")
            return self._extract_config(page, email)

        # Step 3: 点击发送验证码按钮
        self._log("info", "finding and clicking send code button...")
        if not self._click_send_code_button(page):
            self._log("error", "send code button not found")
            self._save_screenshot(page, "send_code_button_missing")
            return {"success": False, "error": "send code button not found"}

        # Step 4: 等待验证码输入框出现
        self._log("info", "waiting for code input field...")
        code_input = self._wait_for_code_input(page)
        if not code_input:
            self._log("error", "code input field not found")
            self._save_screenshot(page, "code_input_missing")
            return {"success": False, "error": "code input not found"}

        # Step 5: 轮询邮件获取验证码（3次，每次5秒间隔）
        self._log("info", "📬 等待邮箱验证码...")
        code = mail_client.poll_for_code(timeout=15, interval=5, since_time=send_time)

        if not code:
            self._log("warning", "⚠️ 验证码超时，15秒后重新发送...")
            time.sleep(15)
            # 更新发送时间（在点击按钮之前记录）
            send_time = datetime.now()
            # 尝试点击重新发送按钮
            if self._click_resend_code_button(page):
                # 再次轮询验证码（3次，每次5秒间隔）
                code = mail_client.poll_for_code(timeout=15, interval=5, since_time=send_time)
                if not code:
                    self._log("error", "❌ 重新发送后仍未收到验证码")
                    self._save_screenshot(page, "code_timeout_after_resend")
                    return {"success": False, "error": "verification code timeout after resend"}
            else:
                self._log("error", "❌ 验证码超时且未找到重新发送按钮")
                self._save_screenshot(page, "code_timeout")
                return {"success": False, "error": "verification code timeout"}

        self._log("info", f"✅ 收到验证码: {code}")

        # Step 6: 输入验证码并提交
        try:
            code_input = page.locator("input[jsname='ovqh0b']").first
            if not code_input.is_visible(timeout=3000):
                code_input = page.locator("input[type='tel']").first
        except Exception:
            code_input = page.locator("input[type='tel']").first

        if not code_input:
            self._log("error", "code input field expired")
            return {"success": False, "error": "code input expired"}

        # 尝试模拟人类输入，失败则降级到直接注入
        self._log("info", "entering verification code (simulating human input)...")
        if not self._simulate_human_input(code_input, code):
            self._log("warning", "simulated input failed, falling back to direct input")
            code_input.fill(code)
            time.sleep(0.5)

        # 直接使用回车提交，不再查找按钮（完全按照 DP 版本）
        self._log("info", "pressing Enter to submit code")
        code_input.press("Enter")

        # Step 7: 等待页面自动重定向（提交验证码后 Google 会自动跳转）
        self._log("info", "waiting for automatic redirect after verification...")
        time.sleep(12)  # 增加等待时间，让页面有足够时间完成重定向

        # 记录当前 URL 状态
        current_url = page.url
        self._log("info", f"URL after verification: {current_url}")

        # 检查是否还停留在验证码页面（说明提交失败）
        if "verify-oob-code" in current_url:
            self._log("error", "verification code submission failed, still on verification page")
            self._save_screenshot(page, "verification_submit_failed")
            return {"success": False, "error": "verification code submission failed"}

        # Step 8: 处理协议页面（如果有）
        self._handle_agreement_page(page)

        # Step 9: 检查是否已经在正确的页面
        current_url = page.url
        has_business_params = "business.gemini.google" in current_url and "csesidx=" in current_url and "/cid/" in current_url

        if has_business_params:
            # 已经在正确的页面，不需要再次导航
            self._log("info", "already on business page with parameters")
            return self._extract_config(page, email)

        # Step 10: 如果不在正确的页面，尝试导航
        if "business.gemini.google" not in current_url:
            self._log("info", "navigating to business page")
            page.goto("https://business.gemini.google/", wait_until="domcontentloaded", timeout=self.timeout)
            time.sleep(5)  # 增加等待时间
            current_url = page.url
            self._log("info", f"URL after navigation: {current_url}")

        # Step 11: 检查是否需要设置用户名
        if "cid" not in page.url:
            if self._handle_username_setup(page):
                time.sleep(5)  # 增加等待时间

        # Step 12: 等待 URL 参数生成（csesidx 和 cid）
        self._log("info", "waiting for URL parameters")
        if not self._wait_for_business_params(page):
            self._log("warning", "URL parameters not generated, trying refresh")
            page.reload(wait_until="domcontentloaded", timeout=self.timeout)
            time.sleep(5)  # 增加等待时间
            if not self._wait_for_business_params(page):
                self._log("error", "URL parameters generation failed")
                current_url = page.url
                self._log("error", f"final URL: {current_url}")
                self._save_screenshot(page, "params_missing")
                return {"success": False, "error": "URL parameters not found"}

        # Step 13: 提取配置
        self._log("info", "login flow complete, extracting config...")
        return self._extract_config(page, email)

    def _click_send_code_button(self, page: Page) -> bool:
        """点击发送验证码按钮（如果需要）"""
        time.sleep(2)

        # 方法1: 直接通过ID查找
        try:
            direct_btn = page.locator("#sign-in-with-email").first
            if direct_btn.is_visible(timeout=5000):
                direct_btn.click()
                self._log("info", "found and clicked send code button (ID: #sign-in-with-email)")
                time.sleep(3)  # 等待发送请求
                return True
        except Exception as e:
            self._log("warning", f"failed to click button: {e}")

        # 方法2: 通过关键词查找（包括更多变体）
        keywords = ["通过电子邮件发送验证码", "通过电子邮件发送", "email", "Email", "Send code", "Send verification", "Verification code", "Send", "发送"]
        try:
            self._log("info", f"searching button by keywords: {keywords}")
            buttons = page.locator("button").all()
            for btn in buttons:
                try:
                    text = (btn.text_content() or "").strip()
                    if text and any(kw.lower() in text.lower() for kw in keywords):
                        self._log("info", f"found matching button: '{text}'")
                        btn.click()
                        self._log("info", "successfully clicked send code button")
                        time.sleep(3)  # 等待发送请求
                        return True
                except Exception as e:
                    self._log("warning", f"failed to click button: {e}")
        except Exception as e:
            self._log("warning", f"button search exception: {e}")

        # 检查是否已经在验证码输入页面（完全按照 DP 版本）
        try:
            code_input = page.locator("input[jsname='ovqh0b']").first
            if code_input.is_visible(timeout=2000):
                self._log("info", "already on code input page, no need to click button")
                return True
        except Exception:
            pass

        try:
            code_input = page.locator("input[name='pinInput']").first
            if code_input.is_visible(timeout=1000):
                self._log("info", "already on code input page, no need to click button")
                return True
        except Exception:
            pass

        self._log("error", "send code button not found")
        return False

    def _wait_for_code_input(self, page: Page, timeout: int = 30):
        """等待验证码输入框出现"""
        selectors = [
            "input[jsname='ovqh0b']",
            "input[type='tel']",
            "input[name='pinInput']",
            "input[autocomplete='one-time-code']",
        ]
        for _ in range(timeout // 2):
            for selector in selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=1000):
                        return el
                except Exception:
                    continue
            time.sleep(2)
        return None

    def _simulate_human_input(self, element, text: str) -> bool:
        """模拟人类输入（逐字符输入，带随机延迟）

        Args:
            element: 输入框元素
            text: 要输入的文本

        Returns:
            bool: 是否成功
        """
        try:
            # 先点击输入框获取焦点
            element.click()
            time.sleep(random.uniform(0.1, 0.3))

            # 逐字符输入
            for char in text:
                element.type(char, delay=random.uniform(50, 150))  # delay in milliseconds

            # 输入完成后短暂停顿
            time.sleep(random.uniform(0.2, 0.5))
            self._log("info", "simulated human input successfully")
            return True
        except Exception as e:
            self._log("warning", f"simulated input failed: {e}")
            return False

    def _click_resend_code_button(self, page: Page) -> bool:
        """点击重新发送验证码按钮"""
        time.sleep(2)

        # 查找包含重新发送关键词的按钮
        try:
            buttons = page.locator("button").all()
            for btn in buttons:
                try:
                    text = (btn.text_content() or "").strip().lower()
                    if text and ("重新" in text or "resend" in text):
                        self._log("info", f"found resend button: {text}")
                        btn.click()
                        time.sleep(2)
                        return True
                except Exception:
                    pass
        except Exception:
            pass

        return False

    def _handle_agreement_page(self, page: Page) -> None:
        """处理协议页面"""
        if "/admin/create" in page.url:
            try:
                agree_btn = page.locator("button.agree-button").first
                if agree_btn.is_visible(timeout=5000):
                    agree_btn.click()
                    time.sleep(2)
            except Exception:
                pass

    def _wait_for_business_params(self, page: Page, timeout: int = 30) -> bool:
        """等待业务页面参数生成（csesidx 和 cid）"""
        for _ in range(timeout):
            url = page.url
            if "csesidx=" in url and "/cid/" in url:
                self._log("info", f"business params ready: {url}")
                return True
            time.sleep(1)
        return False

    def _handle_username_setup(self, page: Page) -> bool:
        """处理用户名设置页面"""
        current_url = page.url

        if "auth.business.gemini.google/login" in current_url:
            return False

        selectors = [
            "input[type='text']",
            "input[name='displayName']",
            "input[aria-label*='用户名' i]",
            "input[aria-label*='display name' i]",
        ]

        username_input = None
        for selector in selectors:
            try:
                username_input = page.locator(selector).first
                if username_input.is_visible(timeout=2000):
                    break
            except Exception:
                continue

        if not username_input:
            return False

        suffix = "".join(random.choices(string.ascii_letters + string.digits, k=3))
        username = f"Test{suffix}"

        try:
            # 清空输入框
            username_input.click()
            time.sleep(0.2)
            username_input.fill("")
            time.sleep(0.1)

            # 尝试模拟人类输入，失败则降级到直接注入
            if not self._simulate_human_input(username_input, username):
                self._log("warning", "simulated username input failed, fallback to direct input")
                username_input.fill(username)
                time.sleep(0.3)

            buttons = page.locator("button").all()
            submit_btn = None
            for btn in buttons:
                try:
                    text = (btn.text_content() or "").strip().lower()
                    if any(kw in text for kw in ["确认", "提交", "继续", "submit", "continue", "confirm", "save", "保存", "下一步", "next"]):
                        submit_btn = btn
                        break
                except Exception:
                    continue

            if submit_btn:
                submit_btn.click()
            else:
                username_input.press("Enter")

            time.sleep(5)
            return True
        except Exception:
            return False

    def _extract_config(self, page: Page, email: str) -> dict:
        """提取配置"""
        try:
            if "cid/" not in page.url:
                page.goto("https://business.gemini.google/", wait_until="domcontentloaded", timeout=self.timeout)
                time.sleep(3)

            url = page.url
            if "cid/" not in url:
                return {"success": False, "error": "cid not found"}

            config_id = url.split("cid/")[1].split("?")[0].split("/")[0]
            csesidx = url.split("csesidx=")[1].split("&")[0] if "csesidx=" in url else ""

            cookies = page.context.cookies()
            ses = next((c["value"] for c in cookies if c["name"] == "__Secure-C_SES"), None)
            host = next((c["value"] for c in cookies if c["name"] == "__Host-C_OSES"), None)

            ses_obj = next((c for c in cookies if c["name"] == "__Secure-C_SES"), None)
            # 使用北京时区，确保时间计算正确（Cookie expiry 是 UTC 时间戳）
            beijing_tz = timezone(timedelta(hours=8))
            if ses_obj and "expires" in ses_obj:
                # 将 UTC 时间戳转为北京时间，再减去12小时作为刷新窗口
                cookie_expire_beijing = datetime.fromtimestamp(ses_obj["expires"], tz=beijing_tz)
                expires_at = (cookie_expire_beijing - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                expires_at = (datetime.now(beijing_tz) + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")

            config = {
                "id": email,
                "csesidx": csesidx,
                "config_id": config_id,
                "secure_c_ses": ses,
                "host_c_oses": host,
                "expires_at": expires_at,
            }
            return {"success": True, "config": config}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _save_screenshot(self, page: Page, name: str) -> None:
        """保存截图"""
        try:
            screenshot_dir = os.path.join("data", "automation")
            os.makedirs(screenshot_dir, exist_ok=True)
            path = os.path.join(screenshot_dir, f"{name}_{int(time.time())}.png")
            page.screenshot(path=path)
        except Exception:
            pass

    def _log(self, level: str, message: str) -> None:
        """记录日志"""
        if self.log_callback:
            try:
                self.log_callback(level, message)
            except TaskCancelledError:
                raise
            except Exception:
                pass

    @staticmethod
    def _get_ua() -> str:
        """生成随机User-Agent"""
        v = random.choice(["120.0.0.0", "121.0.0.0", "122.0.0.0"])
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v} Safari/537.36"
