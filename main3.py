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
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
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

def scrape_match_odds2(driver, match_url):
    """
    Extract betting odds for a specific match.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance.
        match_url (str): URL of the match page to scrape.
    
    Returns:
        list: A list of dictionaries containing betting provider names and their odds.
    """
    print(f"Scraping odds for match: {match_url}")
    driver = setup_driver()
    odds_data = []

    try:
        # Load the match page
        driver.get(match_url)

        # Handle cookie consent
        handle_cookie_consent(driver)

        # Wait for the betting section to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "betting-section")))

        # Locate the betting section
        betting_section = driver.find_element(By.CLASS_NAME, "betting-section")
        
        # Extract team names
        team_cells = betting_section.find_elements(By.CSS_SELECTOR, "tr:first-child td.team-cell")
        
        team_1_name = team_cells[0].text.strip()
        team_2_name = team_cells[-1].text.strip()

        # Locate provider rows
        provider_rows = betting_section.find_elements(By.CSS_SELECTOR, "tr.provider")

        for provider in provider_rows:
            try:
                # Skip rows with the "noOdds" class
                if "noOdds" in provider.get_attribute("class"):
                    continue

                # Check for odds cells
                odds_cells = provider.find_elements(By.CSS_SELECTOR, "td.odds-cell.border-left")

                # Extract provider name
                provider_logo = provider.find_element(By.CSS_SELECTOR, "a.betting-logo-link")
                provider_name = provider_logo.get_attribute("aria-label")

                # Extract odds for Team 1 and Team 2
                team_1_odds = odds_cells[0].find_element(By.TAG_NAME, "a").text.strip() if odds_cells[0].find_elements(By.TAG_NAME, "a") else "-"
                team_2_odds = odds_cells[-1].find_element(By.TAG_NAME, "a").text.strip() if odds_cells[-1].find_elements(By.TAG_NAME, "a") else "-"

                # Ensure odds are valid (numbers, not "-")
                if not team_1_odds.replace('.', '', 1).isdigit() or not team_2_odds.replace('.', '', 1).isdigit():
                    print(f"Invalid odds detected for provider: {provider_name}")
                    continue

                # Append valid provider data to the result
                odds_data.append({
                    "provider": provider_name,
                    team_1_name: team_1_odds,
                    team_2_name: team_2_odds,
                })

            except Exception as e:
                print(f"Error processing provider row: {e}")
                continue

    except Exception as e:
        print(f"Error scraping match odds: {e}")

    return odds_data


def scrape_match_odds(driver, match_url):
    """
    Extract betting odds for a specific match.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance.
        match_url (str): URL of the match page to scrape.
    
    Returns:
        dict: Contains 'teams' (list of team names) and 'odds' (list of provider odds).
    """
    print(f"Scraping odds for match: {match_url}")
    driver = setup_driver()
    odds_data = []
    team_1_name = ""
    team_2_name = ""

    try:
        # Load the match page
        driver.get(match_url)

        # Handle cookie consent
        handle_cookie_consent(driver)

        # Wait for the betting section to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "betting-section")))

        # Locate the betting section
        betting_section = driver.find_element(By.CLASS_NAME, "betting-section")
        
        # Extract team names
        team_cells = betting_section.find_elements(By.CSS_SELECTOR, "tr:first-child td.team-cell")
        team_1_name = team_cells[0].text.strip()
        team_2_name = team_cells[-1].text.strip()

        # Locate provider rows
        provider_rows = betting_section.find_elements(By.CSS_SELECTOR, "tr.provider")

        for provider in provider_rows:
            try:
                # Skip rows with the "noOdds" class
                if "noOdds" in provider.get_attribute("class"):
                    continue

                # Check for odds cells
                odds_cells = provider.find_elements(By.CSS_SELECTOR, "td.odds-cell.border-left")

                # Extract provider name
                provider_logo = provider.find_element(By.CSS_SELECTOR, "a.betting-logo-link")
                provider_name = provider_logo.get_attribute("aria-label")

                # Extract odds for Team 1 and Team 2
                team_1_odds = odds_cells[0].find_element(By.TAG_NAME, "a").text.strip() if odds_cells[0].find_elements(By.TAG_NAME, "a") else "-"
                team_2_odds = odds_cells[-1].find_element(By.TAG_NAME, "a").text.strip() if odds_cells[-1].find_elements(By.TAG_NAME, "a") else "-"

                # Ensure odds are valid (numbers, not "-")
                if not team_1_odds.replace('.', '', 1).isdigit() or not team_2_odds.replace('.', '', 1).isdigit():
                    print(f"Invalid odds detected for provider: {provider_name}")
                    continue

                # Append valid provider data to the result
                odds_data.append({
                    "provider": provider_name,
                    team_1_name: team_1_odds,
                    team_2_name: team_2_odds,
                })

            except Exception as e:
                print(f"Error processing provider row: {e}")
                continue

    except Exception as e:
        print(f"Error scraping match odds: {e}")

    return {
        'teams': [team_1_name, team_2_name],
        'odds': odds_data
    }


def check_arbitrage(teams, odds_data):
    """
    Check for arbitrage opportunities in the given odds data.
    
    Args:
        teams (list): Team names as [team1, team2].
        odds_data (list): List of provider odds.
    
    Returns:
        dict: Arbitrage details if found, None otherwise.
    """
    team1, team2 = teams[0], teams[1]
    providers = []
    
    for entry in odds_data:
        try:
            provider = entry['provider']
            odds1 = float(entry[team1].replace(',', '.'))
            odds2 = float(entry[team2].replace(',', '.'))
            providers.append({
                'provider': provider,
                team1: odds1,
                team2: odds2
            })
        except (KeyError, ValueError) as e:
            print(f"Skipping provider {entry['provider']}: {e}")
            continue
    
    min_sum = float('inf')
    best_pair = None
    
    for p1 in providers:
        for p2 in providers:
            if p1['provider'] == p2['provider']:
                continue  # Must be different providers
            sum_inv = (1 / p1[team1]) + (1 / p2[team2])
            if sum_inv < min_sum:
                min_sum = sum_inv
                best_pair = (p1, p2)
    
    if min_sum < 1:
        return {
            'team1_provider': best_pair[0]['provider'],
            'team1_odds': best_pair[0][team1],
            'team2_provider': best_pair[1]['provider'],
            'team2_odds': best_pair[1][team2],
            'arbitrage_percent': (1 - min_sum) * 100,
            'total_investment': 100,
            'stake_team1': 100 / (min_sum * best_pair[0][team1]),
            'stake_team2': 100 / (min_sum * best_pair[1][team2])
        }
    else:
        return None

if __name__ == "__main__":
    print("Starting HLTV scraper for the first two matches...")
    print("-" * 50)

    # Scrape matches for today
    matches_for_days = scrape_matches_for_days(days=1)

    if matches_for_days:
        print("\nScraping odds for the first two matches...")
        print("=" * 50)

        driver = setup_driver()
        try:
            # for i, match in enumerate(matches_for_days[:2]):  # Only take the first two matches
            for i, match in enumerate(matches_for_days):  # Only take the first two matches
                print(f"Match {i + 1}: {match['teams'][0]['name']} vs {match['teams'][1]['name']}")
                print(f"Match link: {match['link']}")

                # Scrape odds for the match
                # Scrape odds for the match
                odds_info = scrape_match_odds(driver, match['link'])
                if odds_info['odds']:
                    # print("\nOdds for this match:")
                    # for entry in odds_info['odds']:
                    #     print(f"Provider: {entry['provider']}")
                    #     print(f"{odds_info['teams'][0]}: {entry[odds_info['teams'][0]]}")
                    #     print(f"{odds_info['teams'][1]}: {entry[odds_info['teams'][1]]}")
                    #     print("-" * 30)
                    
                    # Check for arbitrage
                    arbitrage = check_arbitrage(odds_info['teams'], odds_info['odds'])
                    if arbitrage:
                        print("\n*** Arbitrage Opportunity Found! ***")
                        print(f"Bet on {odds_info['teams'][0]} at {arbitrage['team1_provider']} with odds {arbitrage['team1_odds']:.2f}")
                        print(f"Bet on {odds_info['teams'][1]} at {arbitrage['team2_provider']} with odds {arbitrage['team2_odds']:.2f}")
                        print(f"Arbitrage Percentage: {arbitrage['arbitrage_percent']:.2f}%")
                        print(f"Stake on {odds_info['teams'][0]}: ${arbitrage['stake_team1']:.2f}")
                        print(f"Stake on {odds_info['teams'][1]}: ${arbitrage['stake_team2']:.2f}")
                        total_stake = arbitrage['stake_team1'] + arbitrage['stake_team2']
                        profit = arbitrage['total_investment'] / (1 - arbitrage['arbitrage_percent'] / 100) - arbitrage['total_investment']
                        print(f"Total Stake: ${total_stake:.2f}")
                        print(f"Guaranteed Profit: ${profit:.2f}")
                    else:
                        print("\nNo arbitrage opportunity found for this match.")
                else:
                    print("No valid odds found for this match.")
                print("-" * 50)
        finally:
            driver.quit()
    else:
        print("\nNo matches found for today.")
