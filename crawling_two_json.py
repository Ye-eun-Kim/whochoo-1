import json
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# Specify the path to the ChromeDriver executable
chrome_service = Service('./chromedriver-win32/chromedriver.exe')  # Adjust this path

# Initialize the Selenium WebDriver (assuming Chrome)
driver = webdriver.Chrome(service=chrome_service)

# Function to get reviews from an item page with pagination
def get_reviews(item_url):
    driver.get(item_url)
    time.sleep(3)  # Wait for the page to load

    # Simulate clicking the review section
    review_section = driver.find_element(By.CLASS_NAME, 'goods_reputation')
    review_section.click()
    time.sleep(3)  # Wait for the reviews to load

    reviews = []

    # Navigate through the first 10 pages (100 reviews, 10 per page)
    for page_no in range(1, 11):
        if page_no > 1:
            # Click the page number link
            page_link = driver.find_element(By.CSS_SELECTOR, f'div.pageing a[data-page-no="{page_no}"]')
            page_link.click()
            time.sleep(3)  # Wait for the page to load

        # Extract reviews on the current page
        review_elements = driver.find_elements(By.CSS_SELECTOR, 'ul#gdasList > li')

        for review_element in review_elements:
            user_info = review_element.find_element(By.CSS_SELECTOR, 'div.info div.user.clrfix a')
            onclick_attribute = user_info.get_attribute('onclick')
            match = re.search(r"t_profile_name:\s*'([^']*)'", onclick_attribute)
            user_id = match.group(1).strip() if match else 'Unknown'

            score_element = review_element.find_element(By.CSS_SELECTOR, 'div.score_area > span.review_point > span.point')
            date_element = review_element.find_element(By.CSS_SELECTOR, 'div.score_area > span.date')
            content_element = review_element.find_element(By.CSS_SELECTOR, 'div.txt_inner')

            # Extract badges and tags
            badge_elements = review_element.find_elements(By.CSS_SELECTOR, 'div.badge a')
            badges = [badge.text.strip() for badge in badge_elements]

            tag_elements = review_element.find_elements(By.CSS_SELECTOR, 'p.tag span')
            tags = [tag.text.strip() for tag in tag_elements]

            # Clean the score text
            score_text = re.sub(r'5점만점에 ', '', score_element.text).strip()

            # Clean the review content
            review_html = content_element.get_attribute('innerHTML')
            review_text = BeautifulSoup(str(review_html), 'html.parser').get_text(separator=' ').strip()

            reviews.append({
                'user_id': user_id,
                'user_attribute': ', '.join(tags),
                'user_activity': ', '.join(badges),
                'score': score_text,
                'date': date_element.text.strip(),
                'content': review_text
            })

            if len(reviews) >= 15:
                break
        if len(reviews) >= 15:
            break

    # Total number of reviews
    total_reviews_element = driver.find_element(By.CSS_SELECTOR, 'div.star_area > p.total > em')
    total_reviews = int(total_reviews_element.text.strip().replace(',', ''))

    # Average star rating
    average_star_rating_element = driver.find_element(By.CSS_SELECTOR, 'p.num > strong')
    average_star_rating = float(average_star_rating_element.text.strip())

    # Star rating distribution
    star_distribution = {'5점': '0', '4점': '0', '3점': '0', '2점': '0', '1점': '0'}
    star_list_elements = driver.find_elements(By.CSS_SELECTOR, 'ul.graph_list > li')

    for star_element in star_list_elements:
        star_percentage_element = star_element.find_element(By.CLASS_NAME, 'per')
        star_count_element = star_element.find_element(By.CLASS_NAME, 'txt')
        star_percentage = star_percentage_element.text.strip()
        star_count = star_count_element.text.strip()

        star_distribution[star_count] = star_percentage

    # Extract skin type, skin concern, and irritation data
    evaluation_categories = {}
    poll_types = driver.find_elements(By.CSS_SELECTOR, 'dl.poll_type2.type3')
    for poll in poll_types:
        category_name = poll.find_element(By.TAG_NAME, 'dt').text.strip()
        evaluations = poll.find_elements(By.CSS_SELECTOR, 'ul.list > li')
        category_data = {}
        for evaluation in evaluations:
            text = evaluation.find_element(By.CLASS_NAME, 'txt').text.strip()
            percentage = evaluation.find_element(By.CLASS_NAME, 'per').text.strip().replace('%', '')
            category_data[text] = percentage
        evaluation_categories[category_name] = category_data

    return {
        'total_reviews': total_reviews,
        'average_star_rating': average_star_rating,
        'star_distribution': star_distribution,
        'evaluation_categories': evaluation_categories,
        'reviews': reviews
    }

# Function to get item details
def get_item_details(url):
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    items = soup.find_all('div', class_='prd_info')
    if not items:
        raise ValueError("No items found on the page. Check the page structure or the request URL.")

    metadata = []
    review_data = []

    for i in range(2):  # Adjust the range as needed
        item = items[i]
        item_idx = i + 1
        item_brand = item.find('span', {'class': 'tx_brand'}).text.strip()
        item_name = item.find('p', {'class': 'tx_name'}).text.strip()
        item_name = re.sub(r'\[.*?\]', '', item_name).strip()
        item_price = int(item.find('span', {'class': 'tx_cur'}).find('span', {'class': 'tx_num'}).text.strip().replace(',', ''))

        full_item_link = item.find('a')['href']
        raw_review_data = get_reviews(full_item_link)

        item_for_meta = {
            'idx': item_idx,
            'brand': item_brand,
            'name': item_name,
            'price': item_price,
            'total_reviews': raw_review_data['total_reviews'],
            'average_star_rating': raw_review_data['average_star_rating'],
            'star_distribution': raw_review_data['star_distribution'],
            'evaluation_categories': raw_review_data['evaluation_categories']
        }
        metadata.append(item_for_meta)

        for review in raw_review_data['reviews']:
            item_for_review = {
                'idx': item_idx,
                'user_id': review['user_id'],
                'user_attribute': review['user_attribute'],
                'user_activity': review['user_activity'],
                'review_score': review['score'],
                'review_date': review['date'],
                'review_content': review['content']
            }
            review_data.append(item_for_review)

    return metadata, review_data

# URL of the page to crawl
url = 'https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=100000100010014&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=48&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=3&aShowCnt=0&bShowCnt=0&cShowCnt=0&trackingCd=Cat100000100010014_Small&amplitudePageGubun=&t_page=&t_click=&midCategory=%EC%97%90%EC%84%BC%EC%8A%A4%2F%EC%84%B8%EB%9F%BC%2F%EC%95%B0%ED%94%8C&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd='
metadata, review_data = get_item_details(url)

# Write metadata to JSON
with open('metadata.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(metadata, jsonfile, ensure_ascii=False, indent=4)

# Write review data to JSON
with open('review_data.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(review_data, jsonfile, ensure_ascii=False, indent=4)

# Close the WebDriver
driver.quit()
