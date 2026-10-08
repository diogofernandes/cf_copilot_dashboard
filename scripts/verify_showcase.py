from pathlib import Path
from playwright.sync_api import sync_playwright
import os
url=os.environ.get("SHOWCASE_URL","http://localhost:8510/")
shots=Path(__file__).resolve().parents[1] / "docs/screenshots"
with sync_playwright() as p:
 browser=p.chromium.launch()
 page=browser.new_page(viewport={"width":1440,"height":1000})
 errors=[];page.on("pageerror",lambda err:errors.append(str(err)))
 response=page.goto(url)
 assert response.status==200
 page.get_by_text("Ready. Load sample invoices to begin.",exact=True).wait_for()
 assert page.locator("#forecast").is_disabled()
 page.screenshot(path=str(shots/"showcase-desktop.png"))
 page.get_by_role("button",name="Load sample invoices",exact=True).click()
 assert page.locator("#invoices tbody tr").count()==24
 page.get_by_role("button",name="Generate forecast",exact=True).click()
 assert page.locator("#forecast-result tbody tr").count()==7
 with page.expect_download() as download:
  page.get_by_role("button",name="Download forecast CSV",exact=True).click()
 assert "43+ days" in Path(download.value.path()).read_text()
 page.get_by_role("button",name="Run risk predictions",exact=True).click()
 assert page.locator("#ranking-result tbody tr").count()==10
 ids=page.locator("#invoice-select option").evaluate_all("(options)=>options.slice(1).map(o=>o.value)")
 for invoice in ids:
  page.locator("#invoice-select").select_option(invoice)
  assert page.locator("#draft-result").is_hidden()
  page.get_by_role("button",name="Generate collection draft",exact=True).click()
  assert invoice in page.locator("#draft-result").inner_text()
 page.locator("#forecast-result").screenshot(path=str(shots/"showcase-forecast.png"))
 page.locator("#draft-result").screenshot(path=str(shots/"showcase-draft.png"))
 page.get_by_role("tab",name="About the project",exact=True).click()
 assert page.get_by_role("heading",name="The model: XGBoost",exact=True).is_visible()
 assert "recorded XGBoost results" in page.locator("#about").inner_text()
 assert "Built collaboratively" not in page.locator("#about").inner_text()
 page.screenshot(path=str(shots/"showcase-about.png"))
 page.get_by_role("tab",name="Cash Flow Co-Pilot",exact=True).click()
 page.get_by_role("button",name="Reset demo",exact=True).click()
 assert page.locator("#draft").is_disabled()
 assert page.locator("#forecast-result").is_hidden()
 mobile=browser.new_page(viewport={"width":390,"height":844})
 mobile.goto(url);mobile.get_by_text("Ready. Load sample invoices to begin.",exact=True).wait_for()
 assert mobile.evaluate("document.documentElement.scrollWidth<=innerWidth")
 mobile.screenshot(path=str(shots/"showcase-mobile.png"))
 assert not errors,errors
 print("Static showcase passed: 24 invoices, seven intervals, ten invoice drafts, export, tabs, reset and mobile layout.")
 browser.close()
