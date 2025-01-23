from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def handle_cookie_consent(driver):
    """Handle the cookie consent popup"""
    try:
        print("Looking for cookie consent button...")
        wait = WebDriverWait(driver, 10)
        
        cookie_button_selectors = [
            "button#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            ".fc-button-label",
            "button[data-accept-cookies='true']",
            "#acceptAllButton",
            ".accept-cookies-button"
        ]
        
        for selector in cookie_button_selectors:
            try:
                cookie_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"Found cookie consent button with selector: {selector}")
                cookie_button.click()
                print("Successfully accepted cookies")
                time.sleep(1)
                return True
            except Exception:
                continue
                
        print("Cookie consent button not found with known selectors")
        return False
        
    except Exception as e:
        print(f"Error handling cookie consent: {e}")
        return False

def get_match_format(match_element):
    """Extract match format (bo3, bo5, etc)"""
    try:
        meta = match_element.find_element(By.CLASS_NAME, "matchMeta")
        return meta.text.strip()
    except:
        return "Unknown"

def get_team_logo(team_element):
    """Extract team logo URL"""
    try:
        logo = team_element.find_element(By.CLASS_NAME, "matchTeamLogo")
        return logo.get_attribute("src")
    except:
        return None

def get_event_info(match_element):
    """Extract event logo and name"""
    try:
        event_logo = match_element.find_element(By.CLASS_NAME, "matchEventLogo").get_attribute("src")
        event_name = match_element.find_element(By.CLASS_NAME, "matchEventName").text.strip()
        return event_logo, event_name
    except:
        return None, None

def scrape_upcoming_matches():
    print("Setting up Chrome driver...")
    driver = setup_driver()
    matches_by_week = {}
    
    try:
        print("Attempting to access HLTV.org...")
        driver.get('https://www.hltv.org/matches')
        
        handle_cookie_consent(driver)
        
        print("Waiting for page to load...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "upcomingMatchesWrapper")))
        time.sleep(3)
        
        print("Page loaded successfully. Extracting matches...")
        match_elements = driver.find_elements(By.CLASS_NAME, "upcomingMatch")
        
        for match in match_elements:
            try:
                # Get match link
                match_link = match.find_element(By.CSS_SELECTOR, "a.match").get_attribute("href")
                
                # Get match time
                time_element = match.find_element(By.CLASS_NAME, "matchTime")
                match_time = time_element.text.strip()
                unix_time = int(match.get_attribute("data-zonedgrouping-entry-unix"))
                match_datetime = datetime.fromtimestamp(unix_time/1000)
                
                # Get week number for grouping
                week_number = match_datetime.isocalendar()[1]
                week_key = f"Week {week_number} ({match_datetime.strftime('%B %Y')})"
                
                # Get teams
                team_elements = match.find_elements(By.CLASS_NAME, "matchTeam")
                teams = []
                for team_element in team_elements:
                    team_name = team_element.find_element(By.CLASS_NAME, "matchTeamName").text.strip()
                    team_logo = get_team_logo(team_element)
                    teams.append({
                        "name": team_name,
                        "logo": team_logo
                    })
                
                # Get match format
                match_format = get_match_format(match)
                
                # Get event information
                event_logo, event_name = get_event_info(match)
                
                # Create match data structure
                match_data = {
                    'date': match_datetime.strftime('%Y-%m-%d'),
                    'time': match_time,
                    'teams': teams,
                    'format': match_format,
                    'event': {
                        'name': event_name,
                        'logo': event_logo
                    },
                    'link': match_link
                }
                
                # Add to matches by week
                if week_key not in matches_by_week:
                    matches_by_week[week_key] = []
                matches_by_week[week_key].append(match_data)
                
                print(f"Found match: {teams[0]['name']} vs {teams[1]['name']} ({match_time})")
                
            except Exception as e:
                print(f"Error processing match: {e}")
                continue
                
    except Exception as e:
        print(f"Error during scraping: {e}")
        
    finally:
        print("Closing browser...")
        driver.quit()
    
    return matches_by_week


def scrape_matches_this_week():
    print("Setting up Chrome driver...")
    driver = setup_driver()
    matches_this_week = []
    
    try:
        print("Attempting to access HLTV.org...")
        driver.get('https://www.hltv.org/matches')
        
        handle_cookie_consent(driver)
        
        print("Waiting for page to load...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "upcomingMatchesWrapper")))
        time.sleep(3)
        
        print("Page loaded successfully. Extracting matches...")
        match_elements = driver.find_elements(By.CLASS_NAME, "upcomingMatch")
        
        today = datetime.today()
        current_week_number = today.isocalendar()[1]
        
        for match in match_elements:
            try:
                # Get match link
                match_link = match.find_element(By.CSS_SELECTOR, "a.match").get_attribute("href")
                
                # Get match time
                time_element = match.find_element(By.CLASS_NAME, "matchTime")
                match_time = time_element.text.strip()
                unix_time = int(match.get_attribute("data-zonedgrouping-entry-unix"))
                match_datetime = datetime.fromtimestamp(unix_time/1000)
                
                # Check if match is in the current week
                match_week_number = match_datetime.isocalendar()[1]
                if match_week_number != current_week_number:
                    continue
                
                # Get teams
                team_elements = match.find_elements(By.CLASS_NAME, "matchTeam")
                teams = []
                for team_element in team_elements:
                    team_name = team_element.find_element(By.CLASS_NAME, "matchTeamName").text.strip()
                    team_logo = get_team_logo(team_element)
                    teams.append({
                        "name": team_name,
                        "logo": team_logo
                    })
                
                # Get match format
                match_format = get_match_format(match)
                
                # Get event information
                event_logo, event_name = get_event_info(match)
                
                # Create match data structure
                match_data = {
                    'date': match_datetime.strftime('%Y-%m-%d'),
                    'time': match_time,
                    'teams': teams,
                    'format': match_format,
                    'event': {
                        'name': event_name,
                        'logo': event_logo
                    },
                    'link': match_link
                }
                
                matches_this_week.append(match_data)
                
                print(f"Found match: {teams[0]['name']} vs {teams[1]['name']} ({match_time})")
                
            except Exception as e:
                print(f"Error processing match: {e}")
                continue
                
    except Exception as e:
        print(f"Error during scraping: {e}")
        
    finally:
        print("Closing browser...")
        driver.quit()
    
    return matches_this_week

def scrape_matches_for_days(days=5):
    """Scrape matches for a specific number of days starting from today."""
    print("Setting up Chrome driver...")
    driver = setup_driver()
    matches_for_days = []
    
    try:
        print("Attempting to access HLTV.org...")
        driver.get('https://www.hltv.org/matches')
        
        handle_cookie_consent(driver)
        
        print("Waiting for page to load...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "upcomingMatchesWrapper")))
        time.sleep(3)
        
        print("Page loaded successfully. Extracting matches...")
        match_elements = driver.find_elements(By.CLASS_NAME, "upcomingMatch")
        
        today = datetime.today()
        end_date = today + timedelta(days=days)
        
        for match in match_elements:
            try:
                # Get match link
                match_link = match.find_element(By.CSS_SELECTOR, "a.match").get_attribute("href")
                
                # Get match time
                time_element = match.find_element(By.CLASS_NAME, "matchTime")
                match_time = time_element.text.strip()
                unix_time = int(match.get_attribute("data-zonedgrouping-entry-unix"))
                match_datetime = datetime.fromtimestamp(unix_time / 1000)
                
                # Check if match is within the date range
                if not (today <= match_datetime <= end_date):
                    continue
                
                # Get teams
                team_elements = match.find_elements(By.CLASS_NAME, "matchTeam")
                teams = []
                for team_element in team_elements:
                    team_name = team_element.find_element(By.CLASS_NAME, "matchTeamName").text.strip()
                    team_logo = get_team_logo(team_element)
                    teams.append({
                        "name": team_name,
                        "logo": team_logo
                    })
                
                # Get match format
                match_format = get_match_format(match)
                
                # Get event information
                event_logo, event_name = get_event_info(match)
                
                # Create match data structure
                match_data = {
                    'date': match_datetime.strftime('%Y-%m-%d'),
                    'time': match_time,
                    'teams': teams,
                    'format': match_format,
                    'event': {
                        'name': event_name,
                        'logo': event_logo
                    },
                    'link': match_link
                }
                
                matches_for_days.append(match_data)
                
                print(f"Found match: {teams[0]['name']} vs {teams[1]['name']} ({match_time})")
                
            except Exception as e:
                print(f"Error processing match: {e}")
                continue
                
    except Exception as e:
        print(f"Error during scraping: {e}")
        
    finally:
        print("Closing browser...")
        driver.quit()
    
    return matches_for_days

def scrape_match_odds(driver, match_url):
    """Extract betting odds for a specific match."""
    print(f"Scraping odds for match: {match_url}")
    odds_data = []
    
    try:
        driver.get(match_url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "betting-section")))
        
        betting_section = driver.find_element(By.CLASS_NAME, "betting-section")
        providers = betting_section.find_elements(By.CSS_SELECTOR, "tr.provider")
        
        for provider in providers:
            try:
                # Check if odds are present
                odds_cells = provider.find_elements(By.CSS_SELECTOR, "td.odds")
                if not odds_cells:
                    continue
                
                # Extract provider name
                provider_logo = provider.find_element(By.CSS_SELECTOR, "a.betting-logo-link")
                provider_name = provider_logo.get_attribute("aria-label")
                
                # Extract odds
                odds = [cell.text.strip() for cell in odds_cells]
                odds_data.append({
                    "provider": provider_name,
                    "odds": odds
                })
            except Exception as e:
                print(f"Error processing provider row: {e}")
                continue
        
    except Exception as e:
        print(f"Error scraping match odds: {e}")
    return odds_data

if __name__ == "__main__":
    print("Starting HLTV scraper for the first two matches...")
    print("-" * 50)
    
    matches_for_days = scrape_matches_for_days(days=1)  # Scrape matches for today
    
    if matches_for_days:
        print("\nScraping odds for the first two matches...")
        print("=" * 50)
        
        driver = setup_driver()
        try:
            for i, match in enumerate(matches_for_days[:2]):  # Only take the first two matches
                print(f"Match {i + 1}: {match['teams'][0]['name']} vs {match['teams'][1]['name']}")
                print(f"Match link: {match['link']}")
                
                odds = scrape_match_odds(driver, match['link'])
                if odds:
                    print("\nOdds for this match:")
                    for entry in odds:
                        print(f"Provider: {entry['provider']}")
                        print(f"Odds: {entry['odds']}")
                else:
                    print("No valid odds found for this match.")
                print("-" * 50)
        finally:
            driver.quit()
    else:
        print("\nNo matches found for today.")

# if __name__ == "__main__":
#     print("Starting HLTV scraper for specific date range...")
#     print("-" * 50)
    
#     days = 5  # Adjust the number of days as needed
#     matches_for_days = scrape_matches_for_days(days=days)
    
#     if matches_for_days:
#         print(f"\nMatches for the next {days} days:")
#         print("=" * 50)
#         for match in matches_for_days:
#             try:
#                 # Ensure the teams list contains exactly 2 teams
#                 if len(match['teams']) < 2:
#                     print(f"Skipping incomplete match data: {match}")
#                     continue
                
#                 team1 = match['teams'][0]['name']
#                 team2 = match['teams'][1]['name']
#                 event_name = match['event'].get('name', 'Unknown Event')
#                 print(f"{match['date']} {match['time']}: {team1} vs {team2}")
#                 print(f"Format: {match['format']}")
#                 print(f"Event: {event_name}")
#                 print(f"Match link: {match['link']}")
#                 print("-" * 30)
#             except Exception as e:
#                 print(f"Error displaying match: {e}")
#                 continue
#     else:
#         print(f"\nNo matches found for the next {days} days.")


# if __name__ == "__main__":
#     print("Starting HLTV scraper for matches this week...")
#     print("-" * 50)
    
#     matches_this_week = scrape_matches_this_week()
    
#     if matches_this_week:
#         print("\nMatches for this week:")
#         print("=" * 50)
#         for match in matches_this_week:
#             print(f"{match['date']} {match['time']}: {match['teams'][0]['name']} vs {match['teams'][1]['name']}")
#             print(f"Format: {match['format']}")
#             print(f"Event: {match['event']['name']}")
#             print(f"Match link: {match['link']}")
#             print("-" * 30)
#     else:
#         print("\nNo matches for this week were found.")


# if __name__ == "__main__":
#     print("Starting HLTV scraper with Selenium...")
#     print("-" * 50)
    
#     try:
#         import selenium
#         import webdriver_manager
#     except ImportError:
#         print("Required packages not found. Please install them using:")
#         print("pip install selenium webdriver-manager")
#         exit(1)
    
#     matches_by_week = scrape_matches_this_week()
    
#     if matches_by_week:
#         print("\nUpcoming matches by week:")
#         print("=" * 50)
#         for week, matches in matches_by_week.items():
#             print(f"\n{week} - {len(matches)} matches:")
#             print("-" * 50)
#             for match in matches:
#                 print(f"{match['date']} {match['time']}: {match['teams'][0]['name']} vs {match['teams'][1]['name']}")
#                 print(f"Format: {match['format']}")
#                 print(f"Event: {match['event']['name']}")
#                 print(f"Match link: {match['link']}")
#                 print("-" * 30)
#     else:
#         print("\nNo upcoming matches were found.")