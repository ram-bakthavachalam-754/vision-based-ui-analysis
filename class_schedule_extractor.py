#!/usr/bin/env python
"""
Enhanced AI Business Importer - Multi-Page Browsing Algorithm for Gymnastics Schools

This script uses AI + Playwright to intelligently browse through gymnastics school websites,
following links and extracting comprehensive information about classes, programs, and schedules.

Algorithm:
1. Site Discovery - Map website structure and identify key pages
2. Intelligent Navigation - Browse through relevant pages systematically  
3. Deep Content Analysis - Extract detailed information from each page
4. Data Synthesis - Combine and cross-reference information from all sources
5. Quality Assurance - Validate and clean extracted data

Usage:
    python enhanced_ai_business_importer.py --business "Gymnastics Academy" --url "https://www.example-gymnastics.com" --platform "iClassPro" --max-pages 20
    
    Parameters:
    --business: Name of the gymnastics school
    --url: Base URL of the school's website
    --platform: Booking platform used (e.g., iClassPro, Jackrabbit, Amilia)
    --max-pages: Maximum number of pages to analyze (default: 15)
    --headless: Run browser in headless mode (optional)
"""

import asyncio
import requests
import json
import sys
import re
import argparse
import base64
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import time as time_module

# Browser automation
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from openai import AsyncOpenAI
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Load environment variables
load_dotenv()
init()

@dataclass
class PageInfo:
    """Information about a discovered page"""
    url: str
    title: str
    page_type: str  # 'programs', 'staff', 'about', 'contact', 'policies', 'schedule', 'pricing'
    priority: int   # 1=highest, 5=lowest
    visited: bool = False
    content_extracted: bool = False
    links_found: List[str] = field(default_factory=list)
    
@dataclass
class ExtractedContent:
    """Content extracted from a single page"""
    url: str
    page_type: str
    business_info: Dict[str, Any] = field(default_factory=dict)
    programs: List[Dict[str, Any]] = field(default_factory=list)
    instructors: List[Dict[str, Any]] = field(default_factory=list)
    policies: List[str] = field(default_factory=list)
    schedules: List[Dict[str, Any]] = field(default_factory=list)
    pricing: List[Dict[str, Any]] = field(default_factory=list)
    raw_content: str = ""

@dataclass
class ComprehensiveBusinessData:
    """Complete business data from all pages"""
    name: str
    description: str
    category: str
    subcategory: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    email: str
    website: str
    operating_hours: Dict[str, Dict[str, str]]
    programs: List[Dict[str, Any]]
    instructors: List[Dict[str, Any]]
    policies: List[str]
    schedules: List[Dict[str, Any]]
    pricing: List[Dict[str, Any]]
    pages_analyzed: List[str]
    extraction_confidence: float


class EnhancedAIBusinessExtractor:
    """Enhanced AI-powered business extractor with multi-page browsing"""
    
    def __init__(self, openai_api_key: str, headless: bool = True, max_pages: int = 15):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.headless = headless
        self.max_pages = max_pages
        self.discovered_pages: List[PageInfo] = []
        self.extracted_content: List[ExtractedContent] = []
        self.visited_urls: Set[str] = set()
        
    async def extract_comprehensive_business_data(self, business_name: str, base_url: str, platform: str) -> ComprehensiveBusinessData:
        """Extract complete gymnastics program data by browsing through entire website"""
        
        print_status(f"🚀 Starting gymnastics program extraction for {business_name}", "info")
        print_status(f"🌐 Base URL: {base_url}", "info")
        print_status(f"📱 Platform: {platform}", "info")
        print_status(f"📊 Max pages to analyze: {self.max_pages}", "info")
        
        browser = None
        try:
            # Phase 1: Browser Setup
            browser, context, page = await self._setup_browser()
            
            # Phase 2: Site Discovery
            await self._discover_site_structure(page, base_url, business_name)
            
            # Phase 3: Intelligent Navigation & Extraction
            await self._browse_and_extract_content(page, platform)
            
            # Phase 4: Data Synthesis
            comprehensive_data = await self._synthesize_all_data(business_name, base_url)
            
            # Phase 5: Quality Assurance
            await self._validate_and_clean_data(comprehensive_data)
            
            return comprehensive_data
            
        except Exception as e:
            print_status(f"❌ Comprehensive extraction failed: {e}", "error")
            raise
        finally:
            if browser:
                await browser.close()
    
    async def _setup_browser(self) -> Tuple[Browser, BrowserContext, Page]:
        """Setup browser with realistic settings"""
        playwright = await async_playwright().start()
        
        browser = await playwright.chromium.launch(
            headless=self.headless,
            slow_mo=300,  # Slower for more careful browsing
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Add stealth measures
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        return browser, context, page
    
    async def _discover_site_structure(self, page: Page, base_url: str, business_name: str):
        """Phase 2: Discover and map website structure"""
        print_status("🔍 Phase 2: Discovering site structure...", "info")
        
        # Navigate to main page
        await page.goto(base_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Take full-page screenshot of main page
        await page.screenshot(path=f"site_discovery_{business_name.replace(' ', '_')}.png", full_page=True)
        
        # Extract all links using AI vision
        links = await self._discover_important_links(page, base_url)
        
        # Categorize and prioritize pages with strict header-first ordering
        header_pages = []
        other_pages = []
        
        for link in links:
            page_info = await self._categorize_page(link, base_url)
            if page_info and page_info.url not in [p.url for p in self.discovered_pages]:
                # Check if this link came from header/navigation
                is_header_link = await self._is_header_navigation_link(link, base_url)
                
                if is_header_link:
                    page_info.priority = 1  # Force highest priority for header links
                    header_pages.append(page_info)
                    print_status(f"🎯 Header link found: {page_info.page_type} - {page_info.title}", "success")
                else:
                    other_pages.append(page_info)
        
        # STRICT PRIORITIZATION: Header links first, then others
        self.discovered_pages = header_pages + other_pages
        
        # Sort header pages by business importance, keep other pages at end
        header_pages.sort(key=lambda x: x.priority)
        other_pages.sort(key=lambda x: x.priority)
        self.discovered_pages = header_pages + other_pages
        
        print_status(f"📋 Discovered {len(self.discovered_pages)} important pages:", "success")
        for page_info in self.discovered_pages[:10]:  # Show top 10
            print_status(f"   {page_info.priority}. {page_info.page_type}: {page_info.title}", "info")
    
    async def _discover_important_links(self, page: Page, base_url: str) -> List[str]:
        """Use AI to identify important links on the page"""
        
        # Take full-page screenshot and get page content
        screenshot_bytes = await page.screenshot(full_page=True)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
        
        # Get links with navigation hierarchy priority
        all_links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(link => {
                    // Determine link location and priority
                    let location = 'content';
                    let priority = 3;
                    
                    // Check if link is in header/navigation (HIGHEST PRIORITY)
                    const headerSelectors = ['header', 'nav', '.navbar', '.navigation', '.main-nav', '.primary-nav', '.header-nav', '.top-nav'];
                    for (const selector of headerSelectors) {
                        const headerElement = document.querySelector(selector);
                        if (headerElement && headerElement.contains(link)) {
                            location = 'header';
                            priority = 1;
                            break;
                        }
                    }
                    
                    // Check if link is in main menu/navigation
                    const menuSelectors = ['.menu', '.main-menu', '.primary-menu', '.nav-menu', '[role="navigation"]'];
                    if (location !== 'header') {
                        for (const selector of menuSelectors) {
                            const menuElement = document.querySelector(selector);
                            if (menuElement && menuElement.contains(link)) {
                                location = 'menu';
                                priority = 1;
                                break;
                            }
                        }
                    }
                    
                    // Check if link is in sidebar (MEDIUM PRIORITY)
                    const sidebarSelectors = ['.sidebar', '.side-nav', '.secondary-nav', 'aside'];
                    if (priority > 2) {
                        for (const selector of sidebarSelectors) {
                            const sidebarElement = document.querySelector(selector);
                            if (sidebarElement && sidebarElement.contains(link)) {
                                location = 'sidebar';
                                priority = 2;
                                break;
                            }
                        }
                    }
                    
                    // Check if link is in footer (LOWEST PRIORITY)
                    const footerSelectors = ['footer', '.footer', '.site-footer', '.page-footer'];
                    if (priority > 2) {
                        for (const selector of footerSelectors) {
                            const footerElement = document.querySelector(selector);
                            if (footerElement && footerElement.contains(link)) {
                                location = 'footer';
                                priority = 4;
                                break;
                            }
                        }
                    }
                    
                    return {
                        href: link.href,
                        text: link.textContent.trim(),
                        title: link.title || '',
                        className: link.className || '',
                        location: location,
                        priority: priority,
                        parentElement: link.parentElement ? link.parentElement.tagName.toLowerCase() : ''
                    };
                });
            }
        """)
        
        # Filter to internal links and prioritize by location
        domain = urlparse(base_url).netloc
        internal_links = []
        for link in all_links:
            # Skip phone number links and external links
            if (link['href'] and 
                domain in link['href'] and 
                not link['href'].startswith('tel:') and 
                not link['href'].startswith('mailto:') and
                'tel:' not in link['href'].lower()):
                internal_links.append(link)
        
        # Sort links by priority (header/nav first, footer last)
        internal_links.sort(key=lambda x: (x['priority'], x['text'].lower()))
        
        # Separate links by location for better analysis
        header_nav_links = [link for link in internal_links if link['location'] in ['header', 'menu']]
        sidebar_links = [link for link in internal_links if link['location'] == 'sidebar']
        content_links = [link for link in internal_links if link['location'] == 'content']
        footer_links = [link for link in internal_links if link['location'] == 'footer']
        
        # Store header/nav URLs for priority checking
        self._header_nav_urls = set(link['href'] for link in header_nav_links)
        
        print_status(f"🔗 Link analysis: Header/Nav: {len(header_nav_links)}, Sidebar: {len(sidebar_links)}, Content: {len(content_links)}, Footer: {len(footer_links)}", "info")
        print_status(f"🎯 Header/Nav URLs stored: {len(self._header_nav_urls)}", "info")
        
        # Print all header/nav links for debugging
        if header_nav_links:
            print_status(f"\n📋 ALL HEADER/NAVIGATION LINKS FOUND ({len(header_nav_links)}):", "success")
            for i, link in enumerate(header_nav_links, 1):
                link_text = link['text'][:50] + "..." if len(link['text']) > 50 else link['text']
                print_status(f"   {i:2d}. {link_text:<30} → {link['href']}", "info")
            print_status("", "info")  # Empty line for readability
        
        # Use AI to identify the most important links with navigation priority
        prompt = f"""
        Analyze this gymnastics school website and identify the most important internal links to visit for complete class and program information extraction.
        
        NAVIGATION HIERARCHY (prioritize in this order):
        1. HEADER/NAVIGATION LINKS (HIGHEST PRIORITY): {json.dumps(header_nav_links[:20], indent=2)}
        
        2. SIDEBAR LINKS (MEDIUM PRIORITY): {json.dumps(sidebar_links[:10], indent=2)}
        
        3. CONTENT LINKS (LOWER PRIORITY): {json.dumps(content_links[:10], indent=2)}
        
        4. FOOTER LINKS (LOWEST PRIORITY): {json.dumps(footer_links[:5], indent=2)}
        
        Return JSON with the most important links:
        {{
            "important_links": [
                {{
                    "url": "full URL",
                    "text": "link text",
                    "location": "header|menu|sidebar|content|footer",
                    "importance": "high|medium|low",
                    "reason": "why this link is important"
                }}
            ]
        }}
        
        STRICT PRIORITIZATION RULES:
        - HEADER/NAVIGATION LINKS ARE MANDATORY - include ALL relevant header/nav links first
        - NEVER skip header/nav links in favor of content or footer links
        - Header/nav links represent the main site structure - these are CRITICAL
        - Include ALL header/nav links that might contain gymnastics program information
        - If header has Programs, Classes, Staff, About, Schedule, Pricing - ALL MUST be included
        - Aim to return 8-15 important links, not just 3-5
        
        Focus on links that would contain GYMNASTICS-SPECIFIC information:
        - Program/class details (recreational gymnastics, competitive team, tumbling, ninja, etc.)
        - Class schedules and session times
        - Staff/coach information
        - Schedules, calendars, and pricing
        - About the gym, policies, and FAQs
        
        AVOID: 
        - Contact pages (can trigger call prompts)
        - Phone number links (tel: links)
        - Email links (mailto: links)
        - External links, social media
        - Generic pages, duplicate content
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=3000,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            
            # Parse AI response
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    important_urls = []
                    for link in result.get('important_links', []):
                        # Accept high, medium, AND low importance links to get more pages
                        if link.get('importance') in ['high', 'medium', 'low']:
                            important_urls.append(link['url'])
                    
                    print_status(f"🔗 AI identified {len(important_urls)} important links", "success")
                    
                    # Show which header links were selected by AI
                    selected_header_links = []
                    selected_other_links = []
                    
                    for link in result.get('important_links', []):
                        if link.get('url') in self._header_nav_urls:
                            selected_header_links.append(link)
                        else:
                            selected_other_links.append(link)
                    
                    if selected_header_links:
                        print_status(f"\n🎯 AI SELECTED HEADER/NAV LINKS ({len(selected_header_links)}):", "success")
                        for i, link in enumerate(selected_header_links, 1):
                            link_text = link.get('text', 'Unknown')[:40]
                            importance = link.get('importance', 'unknown')
                            reason = link.get('reason', 'No reason given')[:60]
                            print_status(f"   {i}. {link_text} ({importance})", "info")
                            print_status(f"      → {reason}", "info")
                    
                    if selected_other_links:
                        print_status(f"\n📄 AI SELECTED OTHER LINKS ({len(selected_other_links)}):", "info")
                        for i, link in enumerate(selected_other_links, 1):
                            link_text = link.get('text', 'Unknown')[:40]
                            importance = link.get('importance', 'unknown')
                            print_status(f"   {i}. {link_text} ({importance})", "info")
                    
                    print_status("", "info")  # Empty line for readability
                    return important_urls
                    
            except json.JSONDecodeError:
                print_status("⚠️ Could not parse AI link analysis", "warning")
        
        except Exception as e:
            print_status(f"⚠️ AI link discovery failed: {e}", "warning")
        
        # Fallback: Use heuristic link filtering
        return self._heuristic_link_filtering(internal_links, base_url)
    
    def _heuristic_link_filtering(self, links: List[Dict], base_url: str) -> List[str]:
        """Fallback heuristic method to identify important links with navigation priority"""
        important_keywords = [
            'program', 'class', 'course', 'lesson', 'staff', 'instructor', 'coach', 'teacher',
            'about', 'schedule', 'calendar', 'pricing', 'price', 'fee', 'cost', 'policy',
            'registration', 'enroll', 'contact', 'location', 'facility'
        ]
        
        # Prioritize links by location and keyword match
        scored_links = []
        for link in links:
            link_text = (link['text'] + ' ' + link.get('title', '')).lower()
            
            # Base score from location priority
            location_scores = {
                'header': 100,
                'menu': 100,
                'sidebar': 50,
                'content': 25,
                'footer': 10
            }
            score = location_scores.get(link.get('location', 'content'), 25)
            
            # Boost score for keyword matches
            keyword_matches = sum(1 for keyword in important_keywords if keyword in link_text)
            score += keyword_matches * 20
            
            # Boost score for common navigation terms
            nav_terms = ['programs', 'classes', 'staff', 'about', 'contact', 'schedule', 'pricing']
            nav_matches = sum(1 for term in nav_terms if term in link_text)
            score += nav_matches * 30
            
            if score > 30:  # Only include links with decent scores
                scored_links.append((link['href'], score, link.get('location', 'content')))
        
        # Sort by score (highest first) and take top links
        scored_links.sort(key=lambda x: x[1], reverse=True)
        
        # Prefer header/nav links even if they have lower keyword scores
        header_nav_links = [link[0] for link in scored_links if link[2] in ['header', 'menu']]
        other_links = [link[0] for link in scored_links if link[2] not in ['header', 'menu']]
        
        # Combine with header/nav links first - be more generous with limits
        important_links = header_nav_links[:15] + other_links[:10]
        
        print_status(f"🎯 Heuristic filtering: {len(header_nav_links)} nav links, {len(other_links)} other links", "info")
        
        # Remove duplicates and limit - increased from 20 to 25
        return list(dict.fromkeys(important_links))[:25]  # Preserve order while removing dupes
    
    async def _is_header_navigation_link(self, url: str, base_url: str) -> bool:
        """Check if a URL was found in header/navigation links"""
        # This is determined during the link discovery phase
        # We'll check the stored link data to see if it came from header/nav
        return hasattr(self, '_header_nav_urls') and url in getattr(self, '_header_nav_urls', set())
    
    async def _categorize_page(self, url: str, base_url: str) -> Optional[PageInfo]:
        """Categorize a page and assign priority - more inclusive approach"""
        
        # Extract page info from URL and text
        url_lower = url.lower()
        
        # HIGHEST PRIORITY: Detailed class/schedule pages (these have actual session details)
        # Pages like /portal/classes, /classes, /schedule-details often have the real data
        if any(word in url_lower for word in ['/portal/class', '/portal/schedule', '/classes/', '/class-schedule', '/sessions', '/register']):
            page_type = 'schedule'
            priority = 1  # HIGHEST - these pages have actual dates, times, availability
            print_status(f"🎯 Found detailed class/schedule page: {url}", "success")
        
        # Schedule/Calendar pages with actual times and dates
        elif any(word in url_lower for word in ['schedule', 'calendar', 'timetable', 'hours', 'time']):
            page_type = 'schedule'
            priority = 1  # High priority for schedule pages
        
        # Program description pages
        elif any(word in url_lower for word in ['program', 'class', 'course', 'lesson', 'academy', 'gymnastics', 'tumbling', 'ninja', 'preschool', 'camp', 'adaptive', 'boys', 'girls', 'xcel', 'team']):
            page_type = 'programs'
            priority = 2  # Lower than schedule pages, but still important
        
        # Staff/instructor pages
        elif any(word in url_lower for word in ['staff', 'instructor', 'coach', 'teacher', 'employee']):
            page_type = 'staff'
            priority = 3
        
        # Pricing pages
        elif any(word in url_lower for word in ['pricing', 'price', 'fee', 'cost', 'tuition', 'payment', 'rate']):
            page_type = 'pricing'
            priority = 2
        
        # About pages
        elif any(word in url_lower for word in ['about', 'story', 'mission', 'history', 'us']):
            page_type = 'about'
            priority = 4
        
        # Policy pages
        elif any(word in url_lower for word in ['policy', 'rule', 'requirement', 'waiver', 'faq', 'policies']):
            page_type = 'policies'
            priority = 4
        
        # Skip contact pages
        elif any(word in url_lower for word in ['contact', 'location', 'address', 'direction']):
            return None
        
        # Special events/programs
        elif any(word in url_lower for word in ['event', 'open-gym', 'field-trip', 'special', 'play-group']):
            page_type = 'programs'
            priority = 2
        
        # Job pages
        elif any(word in url_lower for word in ['job', 'career', 'employment', 'application']):
            page_type = 'about'
            priority = 5
        
        else:
            # Be more inclusive - don't reject pages, categorize as general
            page_type = 'general'
            priority = 4
        
        # Skip if priority too low
        if priority > 5:
            return None
        
        return PageInfo(
            url=url,
            title=url.split('/')[-1].replace('-', ' ').replace('_', ' ').title(),
            page_type=page_type,
            priority=priority
        )
    
    async def _browse_and_extract_content(self, page: Page, platform: str):
        """Phase 3: Browse through pages and extract content with strict header-first priority"""
        print_status("🌐 Phase 3: Browsing and extracting content...", "info")
        
        # Separate header pages from other pages
        header_pages = [p for p in self.discovered_pages if not p.visited and p.priority == 1]
        other_pages = [p for p in self.discovered_pages if not p.visited and p.priority > 1]
        
        # STRICT HEADER-FIRST: Visit ALL header pages before ANY other pages
        pages_to_visit = header_pages + other_pages
        pages_to_visit = pages_to_visit[:self.max_pages]
        
        print_status(f"🎯 Browsing strategy: {len(header_pages)} header pages first, then {len(other_pages)} other pages", "info")
        
        for i, page_info in enumerate(pages_to_visit, 1):
            page_source = "🎯 HEADER" if page_info.priority == 1 else "📄 OTHER"
            print_status(f"{page_source} Visiting page {i}/{len(pages_to_visit)}: {page_info.page_type} - {page_info.title}", "info")
            
            try:
                # Navigate to page
                await page.goto(page_info.url, wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # Mark as visited
                page_info.visited = True
                self.visited_urls.add(page_info.url)
                
                # Take full-page screenshot
                screenshot_path = f"page_{i}_{page_info.page_type}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                # Extract content based on page type
                content = await self._extract_page_content(page, page_info, platform)
                if content:
                    self.extracted_content.append(content)
                    page_info.content_extracted = True
                
                # Rate limiting
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print_status(f"⚠️ Failed to extract from {page_info.url}: {e}", "warning")
                continue
        
        print_status(f"✅ Successfully extracted content from {len(self.extracted_content)} pages", "success")
    
    async def _extract_page_content(self, page: Page, page_info: PageInfo, platform: str) -> Optional[ExtractedContent]:
        """Extract content from a specific page based on its type with intelligent scrolling"""
        
        # Phase 1: Intelligent scrolling to reveal all content
        await self._intelligent_scroll_and_expand(page)
        
        # Phase 2: Take comprehensive screenshots
        screenshots = await self._capture_comprehensive_screenshots(page)
        
        # Phase 3: Get complete page text
        page_text = await page.inner_text('body')
        
        # Create extraction prompt based on page type
        prompt = self._create_extraction_prompt(page_info.page_type, platform, page_text[:5000])  # More text now that we have full page
        
        try:
            # Use the best screenshot for AI analysis (full page if available)
            best_screenshot = screenshots[0] if screenshots else ""
            
            if not best_screenshot:
                print_status("⚠️ No screenshots available for AI analysis", "warning")
                return None
            
            # Enhanced prompt for full-page analysis
            enhanced_prompt = f"""
            IMPORTANT: This is a FULL-PAGE screenshot showing ALL content on the page, including content that was below the fold.
            The page was systematically scrolled and all collapsible content was expanded before taking this screenshot.
            
            {prompt}
            
            Please analyze the ENTIRE image carefully, including all sections from top to bottom.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": enhanced_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{best_screenshot}"}
                            }
                        ]
                    }
                ],
                max_tokens=3000,  # More tokens for comprehensive analysis
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            
            # Parse response and create content object
            content = ExtractedContent(
                url=page_info.url,
                page_type=page_info.page_type,
                raw_content=page_text[:1000]  # Store sample for debugging
            )
            
            # Parse AI response based on page type
            parsed_data = self._parse_ai_response(response_text, page_info.page_type)
            
            # Populate content object and add source page tracking
            if page_info.page_type == 'programs':
                programs = parsed_data.get('programs', [])
                # Add source page info to each program
                for program in programs:
                    program['_source_page'] = page_info.url
                content.programs = programs
            elif page_info.page_type == 'staff':
                content.instructors = parsed_data.get('instructors', [])
            elif page_info.page_type == 'schedule':
                schedules = parsed_data.get('schedules', [])
                # Convert schedules to programs with schedule info
                for schedule in schedules:
                    program_name = schedule.get('program', 'Unknown Program')
                    schedule_program = {
                        'name': program_name,
                        'schedule': f"{schedule.get('day', '')} {schedule.get('time', '')}",
                        'instructor': schedule.get('instructor', ''),
                        'duration': schedule.get('duration', 60),
                        '_source_page': page_info.url
                    }
                    content.programs.append(schedule_program)
                content.schedules = schedules
            elif page_info.page_type == 'pricing':
                pricing = parsed_data.get('pricing', [])
                # Convert pricing to programs with price info
                for price in pricing:
                    program_name = price.get('program', 'Unknown Program')
                    price_program = {
                        'name': program_name,
                        'price': price.get('price', ''),
                        'billing_frequency': price.get('billing_frequency', ''),
                        '_source_page': page_info.url
                    }
                    content.programs.append(price_program)
                content.pricing = pricing
            elif page_info.page_type == 'policies':
                content.policies = parsed_data.get('policies', [])
            elif page_info.page_type in ['about', 'contact']:
                content.business_info = parsed_data.get('business_info', {})
            
            return content
            
        except Exception as e:
            print_status(f"⚠️ AI extraction failed for {page_info.url}: {e}", "warning")
            return None
    
    def _create_extraction_prompt(self, page_type: str, platform: str, page_text: str) -> str:
        """Create specialized extraction prompt based on page type"""
        
        base_prompt = f"This is a {page_type} page from a gymnastics school website using {platform} platform.\n\nPage content:\n{page_text}\n\n"
        
        if page_type == 'programs':
            return base_prompt + """
            Extract detailed gymnastics program information. Look for:
            - Recreational gymnastics classes (by age and level)
            - Competitive team programs (boys/girls team, Xcel, etc.)
            - Tumbling and trampoline classes
            - Ninja/obstacle course programs
            - Preschool/toddler classes
            - Special programs (adaptive, camps, clinics, etc.)
            
            Return JSON:
            {
                "programs": [
                    {
                        "name": "program name",
                        "description": "detailed description of what the class offers",
                        "age_range": [min_months, max_months],
                        "level": "skill level (beginner, intermediate, advanced, team, etc.)",
                        "duration": 60,
                        "max_participants": 12,
                        "skills": ["specific gymnastics skills taught"],
                        "prerequisites": "requirements or prior experience needed",
                        "schedule": "when offered (days/times if available on this page)",
                        "schedule_details": {
                            "days": ["Monday", "Wednesday"],
                            "times": ["4:30 PM - 5:30 PM"],
                            "session_info": "Fall 2025, Spring 2026, etc. if mentioned"
                        },
                        "price": "cost information if available",
                        "additional_info": "any other important details"
                    }
                ]
            }
            
            NOTE: This page may have program DESCRIPTIONS but limited schedule details. 
            Extract whatever schedule information is available, even if limited.
            """
        
        elif page_type == 'staff':
            return base_prompt + """
            Extract gymnastics coach/staff information. Return JSON:
            {
                "instructors": [
                    {
                        "name": "full name",
                        "title": "position/title (Head Coach, Team Coach, Recreational Coach, etc.)",
                        "specialties": ["areas of expertise (e.g., boys team, girls team, tumbling, preschool, etc.)"],
                        "experience": "years or description of coaching experience",
                        "certifications": ["USA Gymnastics certification, SafeSport, First Aid, etc."],
                        "bio": "biography or background",
                        "photo_url": "photo URL if available"
                    }
                ]
            }
            """
        
        elif page_type == 'schedule':
            return base_prompt + """
            Extract DETAILED schedule/class session information. This page likely contains the actual class listings with dates, times, and availability.
            
            For EACH class session, extract ALL available details:
            
            Return JSON:
            {
                "schedules": [
                    {
                        "program": "program/class name",
                        "session_name": "session identifier (e.g., 'Fall 2025', 'Session 1', 'January Classes')",
                        "day": "day of week (Monday, Tuesday, etc.)",
                        "time": "start time (e.g., '4:30 PM', '16:30')",
                        "end_time": "end time if available",
                        "duration": 60,
                        "start_date": "session start date (MM/DD/YYYY or text)",
                        "end_date": "session end date (MM/DD/YYYY or text)",
                        "age_range": "age or age range (e.g., '5-7 years', '3-4')",
                        "level": "skill level (beginner, intermediate, advanced, etc.)",
                        "instructor": "instructor/coach name",
                        "location": "room/area/gym location",
                        "spots_available": "number of spots available (extract number if shown)",
                        "total_spots": "total class size if shown",
                        "status": "registration status (Open, Waitlist, Full, Closed, etc.)",
                        "price": "price if shown on this page",
                        "registration_deadline": "registration deadline if mentioned",
                        "additional_info": "any other relevant details (makeup classes, holidays, etc.)"
                    }
                ]
            }
            
            IMPORTANT: 
            - Extract EVERY class session you see, even if same program has multiple times
            - Look for actual dates, not just "Monday" - extract start/end dates of sessions
            - Capture availability numbers if shown (e.g., "3 spots left" → spots_available: 3)
            - Include age ranges and levels shown with each specific class time
            - Look for session periods (Fall 2025, Spring 2026, Summer camps, etc.)
            """
        
        elif page_type == 'pricing':
            return base_prompt + """
            Extract pricing information. Return JSON:
            {
                "pricing": [
                    {
                        "program": "program name",
                        "price": "cost",
                        "billing_frequency": "monthly/weekly/per class",
                        "packages": ["package options"],
                        "discounts": ["available discounts"],
                        "additional_fees": ["extra costs"]
                    }
                ]
            }
            """
        
        elif page_type == 'policies':
            return base_prompt + """
            Extract policies and rules. Return JSON:
            {
                "policies": [
                    "policy text or rule"
                ]
            }
            """
        
        else:  # about, contact, general
            return base_prompt + """
            Extract gymnastics facility information. Return JSON:
            {
                "business_info": {
                    "name": "gymnastics school/gym name",
                    "description": "description of the gym and its offerings",
                    "address": "full address",
                    "phone": "phone number",
                    "email": "email",
                    "hours": "operating hours or class schedule hours",
                    "history": "background info about the gym",
                    "mission": "mission statement or philosophy",
                    "facility_details": "information about equipment, space, amenities"
                }
            }
            """
    
    def _parse_ai_response(self, response_text: str, page_type: str) -> Dict[str, Any]:
        """Parse AI response and extract JSON data"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {}
    
    async def _synthesize_all_data(self, business_name: str, base_url: str) -> ComprehensiveBusinessData:
        """Phase 4: Combine and synthesize data from all pages"""
        print_status("🔄 Phase 4: Synthesizing data from all pages...", "info")
        
        # Combine all extracted data
        all_programs = []
        all_instructors = []
        all_policies = []
        all_schedules = []
        all_pricing = []
        business_info = {}
        
        for content in self.extracted_content:
            all_programs.extend(content.programs)
            all_instructors.extend(content.instructors)
            all_policies.extend(content.policies)
            all_schedules.extend(content.schedules)
            all_pricing.extend(content.pricing)
            
            # Merge business info
            if content.business_info:
                business_info.update(content.business_info)
        
        # Remove duplicates and clean data
        all_programs = self._deduplicate_programs(all_programs)
        all_instructors = self._deduplicate_instructors(all_instructors)
        all_policies = list(set(all_policies))  # Simple deduplication
        
        # Create comprehensive business data
        comprehensive_data = ComprehensiveBusinessData(
            name=business_info.get('name', business_name),
            description=business_info.get('description', f"Quality gymnastics programs at {business_name}"),
            category="SPORTS",  # Gymnastics schools fall under sports category
            subcategory="GYMNASTICS",
            address=business_info.get('address', 'Address not available'),
            city=business_info.get('city', 'City not available'),
            state=business_info.get('state', 'State not available'),
            zip_code=business_info.get('zip_code', '00000'),
            phone=business_info.get('phone', 'Phone not available'),
            email=business_info.get('email', 'Email not available'),
            website=base_url,
            operating_hours=self._parse_operating_hours(business_info.get('hours', '')),
            programs=all_programs,
            instructors=all_instructors,
            policies=all_policies,
            schedules=all_schedules,
            pricing=all_pricing,
            pages_analyzed=[content.url for content in self.extracted_content],
            extraction_confidence=self._calculate_confidence()
        )
        
        return comprehensive_data
    
    def _deduplicate_programs(self, programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Intelligently merge programs found across multiple pages"""
        return self._merge_cross_page_programs(programs)
    
    def _merge_cross_page_programs(self, programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Advanced program merging that combines information from multiple pages"""
        
        # Group programs by similar names
        program_groups = {}
        
        for program in programs:
            name = program.get('name', '').strip()
            if not name:
                continue
            
            # Normalize name for matching
            normalized_name = self._normalize_program_name(name)
            
            if normalized_name not in program_groups:
                program_groups[normalized_name] = []
            
            program_groups[normalized_name].append(program)
        
        # Merge information within each group
        merged_programs = []
        for normalized_name, group in program_groups.items():
            merged_program = self._merge_program_group(group)
            if merged_program:
                merged_programs.append(merged_program)
                print_status(f"🔗 Merged {len(group)} entries for program: {merged_program['name']}", "success")
        
        return merged_programs
    
    def _normalize_program_name(self, name: str) -> str:
        """Normalize program names for better matching across pages"""
        # Convert to lowercase and remove common variations
        normalized = name.lower().strip()
        
        # Remove common prefixes/suffixes that might vary
        prefixes_to_remove = ['class:', 'program:', 'course:', 'lesson:']
        suffixes_to_remove = ['class', 'program', 'course', 'lesson', 'classes', 'programs']
        
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Handle common variations
        variations = {
            'gymnastics': ['gymnastic', 'gym'],
            'tumbling': ['tumble'],
            'beginner': ['begin', 'starter', 'intro', 'basic'],
            'intermediate': ['inter', 'middle'],
            'advanced': ['adv', 'expert'],
            'preschool': ['pre-school', 'pre school', 'toddler']
        }
        
        for standard, variants in variations.items():
            for variant in variants:
                if variant in normalized:
                    normalized = normalized.replace(variant, standard)
        
        return normalized
    
    def _merge_program_group(self, programs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple program entries into one comprehensive program"""
        if not programs:
            return None
        
        # Start with the first program as base
        merged = programs[0].copy()
        
        # Merge information from all programs in the group
        for program in programs[1:]:
            merged = self._merge_two_programs(merged, program)
        
        # Add source information for debugging
        merged['_sources'] = len(programs)
        merged['_source_pages'] = list(set(p.get('_source_page', 'unknown') for p in programs))
        
        return merged
    
    def _merge_two_programs(self, program1: Dict[str, Any], program2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two program dictionaries intelligently - combines info from description pages and schedule pages"""
        merged = program1.copy()
        
        # Merge strategy for each field
        merge_strategies = {
            'name': self._merge_names,
            'description': self._merge_descriptions,
            'age_range': self._merge_age_ranges,
            'level': self._merge_levels,
            'instructors': self._merge_lists,
            'skills': self._merge_lists,
            'schedule': self._merge_schedules,
            'schedule_details': self._merge_schedule_details,
            'price': self._merge_prices,
            'duration': self._merge_numbers_max,
            'max_participants': self._merge_numbers_max,
            'prerequisites': self._merge_descriptions,
            'category': self._merge_categories,
            'session_name': self._merge_session_info,
            'start_date': self._merge_dates,
            'end_date': self._merge_dates,
            'spots_available': self._merge_availability,
            'total_spots': self._merge_numbers_max,
            'status': self._merge_status,
            'registration_deadline': self._merge_dates,
            'additional_info': self._merge_descriptions
        }
        
        for field, strategy in merge_strategies.items():
            if field in program2 and program2[field]:
                merged[field] = strategy(merged.get(field), program2[field])
        
        return merged
    
    def _merge_names(self, name1: str, name2: str) -> str:
        """Choose the more descriptive name"""
        if not name1:
            return name2
        if not name2:
            return name1
        
        # Prefer longer, more descriptive names
        return name1 if len(name1) >= len(name2) else name2
    
    def _merge_descriptions(self, desc1: str, desc2: str) -> str:
        """Combine descriptions intelligently"""
        if not desc1:
            return desc2
        if not desc2:
            return desc1
        
        # If descriptions are very different, combine them
        if desc1.lower() != desc2.lower():
            return f"{desc1}. {desc2}"
        
        # If similar, use the longer one
        return desc1 if len(desc1) >= len(desc2) else desc2
    
    def _merge_age_ranges(self, range1, range2):
        """Merge age ranges by taking the broader range"""
        if not range1:
            return range2
        if not range2:
            return range1
        
        # Handle None values in age ranges
        min_age1 = range1[0] if range1[0] is not None else 0
        min_age2 = range2[0] if range2[0] is not None else 0
        max_age1 = range1[1] if range1[1] is not None else 999
        max_age2 = range2[1] if range2[1] is not None else 999
        
        # Take the broader age range
        min_age = min(min_age1, min_age2)
        max_age = max(max_age1, max_age2)
        
        # Convert back to None if needed
        min_age = min_age if min_age > 0 else None
        max_age = max_age if max_age < 999 else None
        
        return [min_age, max_age]
    
    def _merge_levels(self, level1: str, level2: str) -> str:
        """Choose the most specific level"""
        if not level1:
            return level2
        if not level2:
            return level1
        
        # Prefer specific levels over generic ones
        generic_levels = ['all levels', 'various', 'mixed']
        
        if level1.lower() in generic_levels and level2.lower() not in generic_levels:
            return level2
        if level2.lower() in generic_levels and level1.lower() not in generic_levels:
            return level1
        
        return level1  # Default to first
    
    def _merge_lists(self, list1, list2):
        """Merge two lists, removing duplicates"""
        if not list1:
            return list2 or []
        if not list2:
            return list1 or []
        
        # Combine and deduplicate
        combined = list1 + list2
        return list(set(item.lower().strip() for item in combined if item))
    
    def _merge_schedules(self, schedule1: str, schedule2: str) -> str:
        """Combine schedule information"""
        if not schedule1:
            return schedule2
        if not schedule2:
            return schedule1
        
        # If schedules are different, combine them
        if schedule1.lower() != schedule2.lower():
            return f"{schedule1}; {schedule2}"
        
        return schedule1
    
    def _merge_prices(self, price1: str, price2: str) -> str:
        """Choose the most specific price information"""
        if not price1:
            return price2
        if not price2:
            return price1
        
        # Prefer specific prices over generic ones
        generic_prices = ['contact for pricing', 'varies', 'call for rates']
        
        if price1.lower() in generic_prices and price2.lower() not in generic_prices:
            return price2
        if price2.lower() in generic_prices and price1.lower() not in generic_prices:
            return price1
        
        # If both are specific, combine them
        if price1.lower() != price2.lower():
            return f"{price1} / {price2}"
        
        return price1
    
    def _merge_numbers_max(self, num1, num2):
        """Take the maximum of two numbers"""
        if not num1:
            return num2
        if not num2:
            return num1
        
        return max(num1, num2)
    
    def _merge_categories(self, cat1: str, cat2: str) -> str:
        """Choose the more specific category"""
        if not cat1:
            return cat2
        if not cat2:
            return cat1
        
        # Prefer specific categories over generic ones
        if cat1.lower() == 'general' and cat2.lower() != 'general':
            return cat2
        if cat2.lower() == 'general' and cat1.lower() != 'general':
            return cat1
        
        return cat1
    
    def _merge_schedule_details(self, details1, details2):
        """Merge schedule details dictionaries"""
        if not details1:
            return details2
        if not details2:
            return details1
        
        # Merge dictionaries, preferring more detailed information
        merged = details1.copy() if isinstance(details1, dict) else {}
        if isinstance(details2, dict):
            for key, value in details2.items():
                if key not in merged or not merged[key]:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged[key], list):
                    # Combine lists and remove duplicates
                    merged[key] = list(set(merged[key] + value))
        
        return merged
    
    def _merge_session_info(self, info1: str, info2: str) -> str:
        """Merge session name/info, preferring more specific"""
        if not info1:
            return info2
        if not info2:
            return info1
        
        # Prefer the more specific session info
        if len(info2) > len(info1):
            return info2
        return info1
    
    def _merge_dates(self, date1: str, date2: str) -> str:
        """Merge date fields, preferring actual dates over generic text"""
        if not date1:
            return date2
        if not date2:
            return date1
        
        # Prefer dates with actual numbers/slashes over text
        if any(char.isdigit() for char in date2) and not any(char.isdigit() for char in date1):
            return date2
        if any(char.isdigit() for char in date1) and not any(char.isdigit() for char in date2):
            return date1
        
        # Prefer longer, more detailed dates
        return date2 if len(date2) > len(date1) else date1
    
    def _merge_availability(self, avail1, avail2):
        """Merge availability info, preferring numeric values"""
        if not avail1:
            return avail2
        if not avail2:
            return avail1
        
        # Try to extract numbers if they're strings
        def extract_number(val):
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, str):
                import re
                match = re.search(r'\d+', val)
                if match:
                    return int(match.group())
            return None
        
        num1 = extract_number(avail1)
        num2 = extract_number(avail2)
        
        # Prefer numeric values
        if num2 is not None and num1 is None:
            return avail2
        if num1 is not None and num2 is None:
            return avail1
        
        # If both numeric, take the more recent/specific one (usually the second)
        return avail2
    
    def _merge_status(self, status1: str, status2: str) -> str:
        """Merge registration status, preferring more specific status"""
        if not status1:
            return status2
        if not status2:
            return status1
        
        # Priority order for status
        priority = {
            'closed': 5,
            'full': 4,
            'waitlist': 3,
            'open': 2,
            'upcoming': 1
        }
        
        status1_lower = status1.lower()
        status2_lower = status2.lower()
        
        # Get priorities
        p1 = priority.get(status1_lower, 0)
        p2 = priority.get(status2_lower, 0)
        
        # Return the one with higher priority (more specific)
        return status1 if p1 >= p2 else status2
    
    def _deduplicate_instructors(self, instructors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate instructors based on name"""
        unique_instructors = []
        seen_names = set()
        
        for instructor in instructors:
            name = instructor.get('name', '').lower().strip()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_instructors.append(instructor)
        
        return unique_instructors
    
    def _parse_operating_hours(self, hours_text: str) -> Dict[str, Dict[str, str]]:
        """Parse operating hours text into structured format"""
        # Default hours
        default_hours = {
            "monday": {"open": "09:00", "close": "18:00"},
            "tuesday": {"open": "09:00", "close": "18:00"},
            "wednesday": {"open": "09:00", "close": "18:00"},
            "thursday": {"open": "09:00", "close": "18:00"},
            "friday": {"open": "09:00", "close": "18:00"},
            "saturday": {"open": "09:00", "close": "17:00"},
            "sunday": {"open": "10:00", "close": "16:00"}
        }
        
        # TODO: Implement intelligent hours parsing
        return default_hours
    
    def _calculate_confidence(self) -> float:
        """Calculate extraction confidence based on data completeness"""
        total_pages = len(self.discovered_pages)
        extracted_pages = len(self.extracted_content)
        
        if total_pages == 0:
            return 0.0
        
        return min(1.0, extracted_pages / total_pages)
    
    async def _validate_and_clean_data(self, data: ComprehensiveBusinessData):
        """Phase 5: Validate and clean extracted data"""
        print_status("🔍 Phase 5: Validating and cleaning data...", "info")
        
        # Validate programs
        valid_programs = []
        for program in data.programs:
            if program.get('name') and len(program['name'].strip()) > 0:
                valid_programs.append(program)
        data.programs = valid_programs
        
        # Validate instructors
        valid_instructors = []
        for instructor in data.instructors:
            if instructor.get('name') and len(instructor['name'].strip()) > 0:
                valid_instructors.append(instructor)
        data.instructors = valid_instructors
        
        # Clean policies
        data.policies = [p for p in data.policies if p and len(p.strip()) > 10]
        
        print_status(f"✅ Data validation complete:", "success")
        print_status(f"   Programs: {len(data.programs)}", "info")
        print_status(f"   Instructors: {len(data.instructors)}", "info")
        print_status(f"   Policies: {len(data.policies)}", "info")
        print_status(f"   Schedules: {len(data.schedules)}", "info")
        print_status(f"   Pricing: {len(data.pricing)}", "info")
        print_status(f"   Confidence: {data.extraction_confidence:.1%}", "info")
    
    async def _intelligent_scroll_and_expand(self, page: Page):
        """Intelligently scroll through page and expand hidden content"""
        print_status("📜 Performing intelligent scrolling to reveal all content...", "info")
        
        # Step 1: Get initial page dimensions
        initial_height = await page.evaluate("document.body.scrollHeight")
        print_status(f"📏 Initial page height: {initial_height}px", "info")
        
        # Step 2: Expand common collapsible elements
        await self._expand_collapsible_content(page)
        
        # Step 3: Perform systematic scrolling
        await self._systematic_page_scroll(page)
        
        # Step 4: Handle infinite scroll or lazy loading
        await self._handle_dynamic_content_loading(page)
        
        # Step 5: Final expansion check and scroll to top
        final_height = await page.evaluate("document.body.scrollHeight")
        print_status(f"📏 Final page height: {final_height}px (expanded by {final_height - initial_height}px)", "info")
        
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)
    
    async def _expand_collapsible_content(self, page: Page):
        """Expand dropdowns, accordions, and collapsible sections"""
        print_status("🔍 Expanding collapsible content...", "info")
        
        # Common selectors for expandable content
        expandable_selectors = [
            # Dropdown menus
            'button[aria-expanded="false"]',
            '.dropdown-toggle:not(.show)',
            '[data-toggle="dropdown"]',
            
            # Accordion sections
            '.accordion-header',
            '.collapse:not(.show)',
            '[data-toggle="collapse"]',
            
            # Show more buttons
            'button:has-text("Show more")',
            'button:has-text("Read more")',
            'button:has-text("View all")',
            'a:has-text("See all")',
            'button:has-text("More")',
            'a:has-text("More")',
            
            # Tab navigation
            '.nav-tab:not(.active)',
            '.tab-button:not(.active)',
            
            # Mobile menu toggles
            '.menu-toggle',
            '.hamburger',
            '.mobile-menu-button',
            
            # Common program/class expansion
            '.program-details-toggle',
            '.class-details-toggle',
            '.expand-details',
            '.show-details'
        ]
        
        expanded_count = 0
        
        for selector in expandable_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements[:10]:  # Increased limit for more thorough expansion
                    try:
                        if await element.is_visible():
                            await element.click()
                            await page.wait_for_timeout(800)  # Longer wait for expansion
                            expanded_count += 1
                            print_status(f"🔧 Expanded element: {selector}", "info")
                    except:
                        continue  # Skip if click fails
            except:
                continue  # Skip if selector fails
        
        print_status(f"✅ Expanded {expanded_count} collapsible elements", "success")
    
    async def _systematic_page_scroll(self, page: Page):
        """Scroll through entire page systematically"""
        print_status("📜 Starting systematic page scroll...", "info")
        
        # Get initial page dimensions
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        
        # Calculate scroll steps (overlap by 30% for better context)
        scroll_step = int(viewport_height * 0.7)
        current_position = 0
        scroll_count = 0
        
        print_status(f"📏 Page height: {page_height}px, viewport: {viewport_height}px, step: {scroll_step}px", "info")
        
        # Scroll through page systematically with dynamic content detection
        while current_position < page_height:
            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await page.wait_for_timeout(1200)  # Longer wait for lazy loading
            scroll_count += 1
            
            # Check if new content loaded (page height changed)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > page_height:
                height_increase = new_height - page_height
                page_height = new_height
                print_status(f"📈 Page expanded by {height_increase}px to {page_height}px at scroll {scroll_count}", "success")
            
            # Try to trigger any lazy loading by scrolling slightly past current position
            await page.evaluate(f"window.scrollTo(0, {current_position + scroll_step // 2})")
            await page.wait_for_timeout(500)
            
            current_position += scroll_step
            
            # Safety check to prevent infinite scrolling
            if scroll_count > 50:
                print_status("⚠️ Maximum scroll limit reached", "warning")
                break
        
        # Final scroll to bottom to ensure all content is loaded
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        
        final_height = await page.evaluate("document.body.scrollHeight")
        print_status(f"✅ Systematic scroll complete: {scroll_count} scrolls, final height: {final_height}px", "success")
    
    async def _handle_dynamic_content_loading(self, page: Page):
        """Handle infinite scroll and lazy loading"""
        print_status("🔄 Handling dynamic content loading...", "info")
        
        # Look for "Load more" buttons
        load_more_selectors = [
            'button:has-text("Load more")',
            'button:has-text("Show more")',
            'button:has-text("View more")',
            'a:has-text("Load more")',
            'a:has-text("Show more")',
            '.load-more-button',
            '.show-more-button',
            '.pagination-next',
            '[data-load-more]',
            'button:has-text("See all")',
            'a:has-text("See all")'
        ]
        
        total_clicks = 0
        
        for selector in load_more_selectors:
            try:
                load_button = page.locator(selector).first
                click_count = 0
                
                while await load_button.count() > 0 and click_count < 8:  # Increased max clicks
                    if await load_button.is_visible():
                        await load_button.click()
                        await page.wait_for_timeout(2500)  # Longer wait for content to load
                        click_count += 1
                        total_clicks += 1
                        print_status(f"🔄 Clicked '{selector}' button {click_count} times", "info")
                    else:
                        break
            except:
                continue
        
        # Handle infinite scroll by scrolling to bottom multiple times
        previous_height = await page.evaluate("document.body.scrollHeight")
        
        for i in range(5):  # More attempts
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)  # Longer wait
            
            # Check if more content loaded
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > previous_height:
                height_increase = new_height - previous_height
                print_status(f"📈 Infinite scroll detected: page grew by {height_increase}px", "success")
                previous_height = new_height
            else:
                print_status(f"⏹️ No more content loading after {i+1} scroll attempts", "info")
                break
        
        print_status(f"✅ Dynamic content loading complete: {total_clicks} buttons clicked", "success")
    
    async def _capture_comprehensive_screenshots(self, page: Page) -> List[str]:
        """Capture multiple screenshots covering entire page content"""
        print_status("📸 Capturing comprehensive screenshots...", "info")
        
        screenshots = []
        
        # Get final page dimensions after all scrolling and expansion
        final_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        print_status(f"📏 Final page dimensions: {final_height}px height, {viewport_height}px viewport", "info")
        
        # Method 1: Full page screenshot (best for AI analysis)
        try:
            # Ensure we're at the top before taking full page screenshot
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            full_page_bytes = await page.screenshot(full_page=True, timeout=30000)  # Increased timeout
            full_page_b64 = base64.b64encode(full_page_bytes).decode()
            screenshots.append(full_page_b64)
            print_status(f"📸 Captured full-page screenshot ({len(full_page_b64)} chars)", "success")
        except Exception as e:
            print_status(f"⚠️ Full-page screenshot failed: {e}", "warning")
        
        # Method 2: Viewport screenshots at key positions (fallback or supplement)
        if not screenshots or final_height > 10000:  # Use fallback if no full-page or page is very long
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            # Take screenshots at key positions with more coverage
            num_sections = min(6, max(3, page_height // viewport_height))
            positions = [int(i * page_height / num_sections) for i in range(num_sections)]
            positions.append(max(0, page_height - viewport_height))  # Ensure we get the bottom
            
            print_status(f"📸 Taking {len(positions)} viewport screenshots as fallback/supplement", "info")
            
            for i, pos in enumerate(positions):
                try:
                    await page.evaluate(f"window.scrollTo(0, {max(0, pos)})")
                    await page.wait_for_timeout(800)
                    
                    screenshot_bytes = await page.screenshot(full_page=False, timeout=15000)
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                    screenshots.append(screenshot_b64)
                    
                except Exception as e:
                    print_status(f"⚠️ Viewport screenshot {i+1} failed: {e}", "warning")
            
            print_status(f"📸 Captured {len(screenshots)} total screenshots", "success")
        
        # Reset to top for consistent state
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        
        return screenshots


def print_status(message: str, status: str = "info"):
    """Print a colored status message."""
    status_colors = {
        "info": Fore.BLUE,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED
    }
    color = status_colors.get(status, Fore.WHITE)
    print(f"{color}{message}{Style.RESET_ALL}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced AI Gymnastics Program Importer - Multi-Page Browsing')
    parser.add_argument('--business', required=True, help='Gymnastics school name')
    parser.add_argument('--url', required=True, help='Gymnastics school website base URL')
    parser.add_argument('--platform', required=True, help='Booking platform (e.g., iClassPro, Jackrabbit, Amilia)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--max-pages', type=int, default=15, help='Maximum pages to analyze')
    
    args = parser.parse_args()
    
    print_status("🚀 Enhanced AI Gymnastics Program Importer Starting", "info")
    print_status(f"Gymnastics School: {args.business}", "info")
    print_status(f"Base URL: {args.url}", "info")
    print_status(f"Platform: {args.platform}", "info")
    print_status(f"Max Pages: {args.max_pages}", "info")
    
    try:
        # Get OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print_status("❌ OPENAI_API_KEY environment variable required", "error")
            return
        
        # Extract comprehensive business data
        extractor = EnhancedAIBusinessExtractor(
            openai_key, 
            headless=args.headless, 
            max_pages=args.max_pages
        )
        
        business_data = await extractor.extract_comprehensive_business_data(
            args.business, args.url, args.platform
        )
        
        # Display comprehensive results
        print_status("\n📊 COMPREHENSIVE EXTRACTION RESULTS", "success")
        print_status("=" * 60, "info")
        print_status(f"Business: {business_data.name}", "info")
        print_status(f"Description: {business_data.description}", "info")
        print_status(f"Location: {business_data.city}, {business_data.state}", "info")
        print_status(f"Contact: {business_data.phone} | {business_data.email}", "info")
        print_status(f"Pages Analyzed: {len(business_data.pages_analyzed)}", "info")
        print_status(f"Extraction Confidence: {business_data.extraction_confidence:.1%}", "info")
        
        print_status(f"\n📚 Detailed Programs Found ({len(business_data.programs)}):", "success")
        for i, program in enumerate(business_data.programs, 1):
            print_status(f"  {i}. {program.get('name', 'Unknown')}", "info")
            if program.get('description'):
                desc = program['description'][:100] + "..." if len(program['description']) > 100 else program['description']
                print_status(f"     Description: {desc}", "info")
            if program.get('age_range'):
                print_status(f"     Age Range: {program['age_range']}", "info")
            if program.get('level'):
                print_status(f"     Level: {program['level']}", "info")
            
            # Display detailed schedule information
            if program.get('session_name'):
                print_status(f"     Session: {program['session_name']}", "info")
            if program.get('start_date') or program.get('end_date'):
                date_range = f"{program.get('start_date', 'TBD')} to {program.get('end_date', 'TBD')}"
                print_status(f"     Dates: {date_range}", "info")
            if program.get('schedule'):
                print_status(f"     Schedule: {program['schedule']}", "info")
            if program.get('schedule_details'):
                details = program['schedule_details']
                if details.get('days'):
                    print_status(f"     Days: {', '.join(details['days']) if isinstance(details['days'], list) else details['days']}", "info")
                if details.get('times'):
                    print_status(f"     Times: {', '.join(details['times']) if isinstance(details['times'], list) else details['times']}", "info")
            
            # Display availability
            if program.get('status'):
                print_status(f"     Status: {program['status']}", "info")
            if program.get('spots_available'):
                avail_text = f"{program['spots_available']}"
                if program.get('total_spots'):
                    avail_text += f" / {program['total_spots']}"
                print_status(f"     Availability: {avail_text} spots", "info")
            
            if program.get('price'):
                print_status(f"     Price: {program['price']}", "info")
            if program.get('instructor'):
                print_status(f"     Instructor: {program['instructor']}", "info")
            
            # Show source pages for debugging
            if program.get('_source_pages'):
                pages = program['_source_pages'][:2]  # Show first 2 source pages
                print_status(f"     [Sources: {len(program.get('_source_pages', []))} pages]", "info")
        
        print_status(f"\n👨‍🏫 Detailed Instructors Found ({len(business_data.instructors)}):", "success")
        for instructor in business_data.instructors:
            print_status(f"  - {instructor.get('name', 'Unknown')}", "info")
            if instructor.get('title'):
                print_status(f"    Title: {instructor['title']}", "info")
            if instructor.get('specialties'):
                print_status(f"    Specialties: {', '.join(instructor['specialties'])}", "info")
            if instructor.get('experience'):
                print_status(f"    Experience: {instructor['experience']}", "info")
        
        if business_data.schedules:
            print_status(f"\n📅 Detailed Schedules Found ({len(business_data.schedules)}):", "success")
            for i, schedule in enumerate(business_data.schedules[:10], 1):  # Show first 10
                program_name = schedule.get('program', 'Unknown')
                time_info = f"{schedule.get('day', '')} {schedule.get('time', '')}"
                print_status(f"  {i}. {program_name}: {time_info}", "info")
                
                if schedule.get('session_name'):
                    print_status(f"     Session: {schedule['session_name']}", "info")
                if schedule.get('start_date') or schedule.get('end_date'):
                    date_range = f"{schedule.get('start_date', 'TBD')} to {schedule.get('end_date', 'TBD')}"
                    print_status(f"     Dates: {date_range}", "info")
                if schedule.get('age_range'):
                    print_status(f"     Ages: {schedule['age_range']}", "info")
                if schedule.get('status'):
                    print_status(f"     Status: {schedule['status']}", "info")
                if schedule.get('spots_available'):
                    avail = f"{schedule['spots_available']}"
                    if schedule.get('total_spots'):
                        avail += f" / {schedule['total_spots']}"
                    print_status(f"     Availability: {avail} spots", "info")
                if schedule.get('instructor'):
                    print_status(f"     Instructor: {schedule['instructor']}", "info")
        
        if business_data.pricing:
            print_status(f"\n💰 Pricing Information ({len(business_data.pricing)}):", "success")
            for price in business_data.pricing[:5]:  # Show first 5
                print_status(f"  - {price.get('program', 'Unknown')}: {price.get('price', 'Contact for pricing')}", "info")
        
        print_status(f"\n📋 Policies Found ({len(business_data.policies)}):", "success")
        for policy in business_data.policies[:3]:  # Show first 3
            print_status(f"  - {policy[:100]}...", "info")
        
        print_status(f"\n🌐 Pages Analyzed:", "success")
        for url in business_data.pages_analyzed:
            print_status(f"  - {url}", "info")
        
        print_status(f"\n🎉 Gymnastics program extraction completed!", "success")
        print_status(f"Extracted detailed class and program information from {len(business_data.pages_analyzed)} pages", "success")
        print_status(f"Found {len(business_data.programs)} gymnastics programs/classes", "success")
            
    except Exception as e:
        print_status(f"❌ Error: {e}", "error")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
