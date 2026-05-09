"""
Fixtures Playwright pour les tests E2E - Jour 6.

Fournit les fixtures partagées pour tous les tests E2E :
- page : fixture page Playwright (API synchrone)
- browser_context : contexte avec viewport 1280x720
- base_url : URL de base de l'application via live_server
- screenshot_on_failure : capture automatique d'écran en cas d'échec
- traced_page : page avec trace activée pour le débogage
"""

import os
import pytest
from playwright.sync_api import Page, BrowserContext


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: marquage des tests End-to-End Playwright (Sprint 1, Jour 6)"
    )


@pytest.fixture(scope="session")
def base_url(live_server):
    """URL de base via pytest-django live_server."""
    return live_server.url




@pytest.fixture(scope="function")          # ← was session
def browser_context(browser, base_url):
    """Contexte isolé par test — évite les fuites de session/cookies."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        base_url=base_url,
    )
    yield context
    context.close()


@pytest.fixture(scope="function")          # ← was session
def page(browser_context):
    """Page fraîche pour chaque test."""
    page = browser_context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def screenshot_on_failure(page, request):
    yield page
    failed = getattr(getattr(request.node, "rep_call", None), "failed", False)
    if failed:
        screenshots_dir = os.path.join("test-results", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        page.screenshot(
            path=os.path.join(screenshots_dir, f"{request.node.name}-failure.png"),
            full_page=True,
        )


@pytest.fixture(scope="function")          # ← was session
def traced_page(browser_context, request):
    traces_dir = os.path.join("test-results", "traces")
    os.makedirs(traces_dir, exist_ok=True)

    browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = browser_context.new_page()
    yield page
    page.close()

    failed = getattr(getattr(request.node, "rep_call", None), "failed", False)
    trace_path = os.path.join(traces_dir, f"{request.node.name}-trace.zip")
    if failed:
        browser_context.tracing.stop(path=trace_path)
    else:
        browser_context.tracing.stop()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)