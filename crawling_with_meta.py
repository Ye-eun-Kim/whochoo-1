import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import csv
import re

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
            badge_elements = review_element.find_elements(By.CSS_SELECTOR, 'div.badge a.point_flag')
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
                'score': score_text,
                'date': date_element.text.strip(),
                'content': review_text,
                'badges': ', '.join(badges),
                'tags': ', '.join(tags)
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
            'skin_type_dry': raw_review_data['evaluation_categories']['피부타입'].get('건성에 좋아요', '0'),
            'skin_type_combination': raw_review_data['evaluation_categories']['피부타입'].get('복합성에 좋아요', '0'),
            'skin_type_oily': raw_review_data['evaluation_categories']['피부타입'].get('지성에 좋아요', '0'),
            'skin_concern_moisturizing': raw_review_data['evaluation_categories']['피부고민'].get('보습에 좋아요', '0'),
            'skin_concern_soothing': raw_review_data['evaluation_categories']['피부고민'].get('진정에 좋아요', '0'),
            'skin_concern_wrinkle_whitening': raw_review_data['evaluation_categories']['피부고민'].get('주름/미백에 좋아요', '0'),
            'irritation_non_irritating': raw_review_data['evaluation_categories']['자극도'].get('자극없이 순해요', '0'),
            'irritation_moderate': raw_review_data['evaluation_categories']['자극도'].get('보통이에요', '0'),
            'irritation_irritating': raw_review_data['evaluation_categories']['자극도'].get('자극이 느껴져요', '0')
        }
        metadata.append(item_for_meta)

        for review in raw_review_data['reviews']:
            item_for_review = {
                'idx': item_idx,
                'user_id': review['user_id'],
                'review_score': review['score'],
                'review_date': review['date'],
                'review_content': review['content'],
                'badges': review['badges'],
                'tags': review['tags']
            }
            review_data.append(item_for_review)

    return metadata, review_data

# URL of the page to crawl
url = 'https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=100000100010014&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=48&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=3&aShowCnt=0&bShowCnt=0&cShowCnt=0&trackingCd=Cat100000100010014_Small&amplitudePageGubun=&t_page=&t_click=&midCategory=%EC%97%90%EC%84%BC%EC%8A%A4%2F%EC%84%B8%EB%9F%BC%2F%EC%95%B0%ED%94%8C&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd='
metadata, review_data = get_item_details(url)

# Write metadata to CSV
with open('metadata.csv', 'w', encoding='utf-8', newline='') as csvfile:
    fieldnames = [
        'Idx', 'Brand', 'Product Name', 'Current Price (Won)', 'Total Reviews',
        'Average Star Rating (out of 5)', 'Star Distribution',
        'Skin Type - Dry (%)', 'Skin Type - Combination (%)', 'Skin Type - Oily (%)',
        'Skin Concern - Moisturizing (%)', 'Skin Concern - Soothing (%)', 'Skin Concern - Wrinkle/Whitening (%)',
        'Irritation - Non-irritating (%)', 'Irritation - Moderate (%)', 'Irritation - Irritating (%)'
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for data in metadata:
        writer.writerow({
            'Idx': data['idx'],
            'Brand': data['brand'],
            'Product Name': data['name'],
            'Current Price (Won)': data['price'],
            'Total Reviews': data['total_reviews'],
            'Average Star Rating (out of 5)': data['average_star_rating'],
            'Star Distribution': data['star_distribution'],
            'Skin Type - Dry (%)': data['skin_type_dry'],
            'Skin Type - Combination (%)': data['skin_type_combination'],
            'Skin Type - Oily (%)': data['skin_type_oily'],
            'Skin Concern - Moisturizing (%)': data['skin_concern_moisturizing'],
            'Skin Concern - Soothing (%)': data['skin_concern_soothing'],
            'Skin Concern - Wrinkle/Whitening (%)': data['skin_concern_wrinkle_whitening'],
            'Irritation - Non-irritating (%)': data['irritation_non_irritating'],
            'Irritation - Moderate (%)': data['irritation_moderate'],
            'Irritation - Irritating (%)': data['irritation_irritating']
        })

with open('reviews_data.csv', 'w', encoding='utf-8', newline='') as csvfile:
    fieldnames = ['Index', 'User ID', 'User Attributes', 'User Activity', 'Score (out of 5)', 'Date', 'Review Content']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for review in review_data:
        writer.writerow({
            'Index': review['idx'],
            'User ID': review['user_id'],
            'User Attributes': review['tags'],
            'User Activity': review['badges'],
            'Score (out of 5)': review['review_score'],
            'Date': review['review_date'],
            'Review Content': review['review_content']
        })

# Close the WebDriver
driver.quit()

