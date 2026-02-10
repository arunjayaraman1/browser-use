# Generated from browser-use code-use session
import os

# Disable telemetry to avoid any startup stalls in restricted networks
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")

import asyncio
import json
from browser_use import BrowserSession
from browser_use.code_use import create_namespace

async def main():
	
	print("Starting browser...")
	browser = BrowserSession()
	await browser.start()
	print("Browser ready. Creating namespace...")

	namespace = create_namespace(browser)

	# Extract functions from namespace for direct access
	navigate = namespace["navigate"]
	click = namespace["click"]
	input_text = namespace.get("input_text")
	evaluate = namespace["evaluate"]
	scroll = namespace.get("scroll")
	done = namespace["done"]
	go_back = namespace.get("go_back")
	wait = namespace.get("wait")
	switch_tab = namespace.get("switch")
	close_tab = namespace.get("close")
	dropdown_options = namespace.get("dropdown_options")
	select_dropdown = namespace.get("select_dropdown")
	upload_file = namespace.get("upload_file")
	send_keys = namespace.get("send_keys")

	# JavaScript Code Block: extract_direct_links
	extract_direct_links = """(function(){
	const links = [];
	// Header logo
	const logo = document.querySelector('.logo--default');
	if (logo) {
		links.push({
			link_text: 'PfizerForAll',
			url_value: logo.href,
			selector: '.logo--default'
		});
	}

	// Hero/Carousel link (i_104)
	const heroLink = document.querySelector('.hero-overlay-button-group a.button');
	if (heroLink) {
		links.push({
			link_text: heroLink.title || heroLink.textContent.trim(),
			url_value: heroLink.href,
			selector: '.hero-overlay-button-group a.button'
		});
	}

	// Card Grid links (i_257, i_281)
	document.querySelectorAll('.card-grid-inner .card a.button').forEach(a => {
		links.push({
			link_text: a.title || a.textContent.trim(),
			url_value: a.href,
			selector: '.card-grid-inner .card a.button'
		});
	});

	return links;
})()"""

	# Cell 1
	print("Navigating to https://www.pfizerforall.com ...")
	await navigate('https://www.pfizerforall.com/')


	# Cell 2
	print("Accepting cookies...")
	await click(index=3650) # Accept All cookies
	await asyncio.sleep(1)

	# Cell 3
	direct_links_data = []
	# The logo link text is not explicitly in the DOM, but based on the class 'logo logo--default' and the screenshot, 'PfizerForAll' is the correct text.
	direct_links_data.append({
		'link_text': 'PfizerForAll',
		'url_value': 'https://www.pfizerforall.com/',
		'page_title': 'pfizerforall.com'
	})
	try:
		extracted_links = await evaluate(extract_direct_links)
		for link in extracted_links:
			# Skip the logo if it was extracted again via the selector
			if link['link_text'] == 'PfizerForAll' and link['url_value'] == 'https://www.pfizerforall.com/':
				continue
			# Navigate and verify link
			await navigate(link['url_value'])
			await asyncio.sleep(2)
			# Get page title
			page_title = await evaluate('document.title')
			direct_links_data.append({
				'link_text': link['link_text'],
				'url_value': link['url_value'],
				'page_title': page_title
			})
			# Return to homepage
			await navigate('https://www.pfizerforall.com/')
			await asyncio.sleep(2)
	except Exception as e:
		print(f"Error extracting direct links or navigating: {e}")
	print(f"Extracted {len(direct_links_data)} direct links.")

	# Cell 4
	# Variables to store dropdown data
	dropdown_links_data = []
	dropdown_names = [
		{'name': 'Understand Your Health', 'index': 2281},
		{'name': 'Find the Care You Need', 'index': 2306},
		{'name': 'Get Savings', 'index': 2313},
		{'name': 'Explore Pfizer', 'index': 2327}
	]
	# Function to extract links from the currently open dropdown
	extract_dropdown_links = """
	(function(dropdownName){
		const links = [];
		const menu = document.querySelector('.header-desktop-nav .nav-l1-item.has-submenu.is-open');
		if (!menu) return links;
		// Check for grouped links (usually under h3 or strong/b tags)
		const groups = menu.querySelectorAll('.nav-l2-group');
		if (groups.length > 0) {
			groups.forEach(group => {
				const groupNameEl = group.querySelector('h3, strong, b');
				const groupName = groupNameEl ? groupNameEl.textContent.trim() : 'None';
				group.querySelectorAll('a').forEach(a => {
					links.push({
						dropdown_name: dropdownName,
						group_name: groupName,
						link_text: a.textContent.trim(),
						url_value: a.href
					});
				});
			});
		} else {
			// Check for ungrouped links directly under the main menu container
			menu.querySelectorAll('.nav-l2-link').forEach(a => {
				links.push({
					dropdown_name: dropdownName,
					group_name: 'None',
					link_text: a.textContent.trim(),
					url_value: a.href
				});
			});
		}
		return links;
	})
	"""
	# Iterate through dropdowns
	for dropdown in dropdown_names:
		dropdown_name = dropdown['name']
		index = dropdown['index']
		print(f"Processing dropdown: {dropdown_name} (Index {index})")
		# 1. Click to open the dropdown
		await click(index=index)
		await asyncio.sleep(1) # Wait for menu to open
		# 2. Extract links
		try:
			extracted_links = await evaluate(extract_dropdown_links, variables={'dropdownName': dropdown_name})
			# 3. Process and verify each link
			for link in extracted_links:
				print(f"  Verifying link: {link['link_text']}")
				# Navigate and verify link
				await navigate(link['url_value'])
				await asyncio.sleep(2)
				# Get page title
				page_title = await evaluate('document.title')
				link['page_title'] = page_title
				dropdown_links_data.append(link)
				# Return to homepage
				await navigate('https://www.pfizerforall.com/')
				await asyncio.sleep(2)
				# Re-open the current dropdown for the next link check
				await click(index=index)
				await asyncio.sleep(1)
		except Exception as e:
			print(f"Error processing {dropdown_name}: {e}")
			# If error, ensure we navigate back before trying the next dropdown
			await navigate('https://www.pfizerforall.com/')
			await asyncio.sleep(2)
			continue
		# 4. Close the dropdown (by clicking the trigger again or navigating away, but navigating away is already done)
	print(f"Total extracted dropdown links: {len(dropdown_links_data)}")

	# Cell 5
	gherkin_template = """Feature: Validate all navigation links
	Background:
	  Given I am on "https://www.pfizerforall.com/"
	Scenario Outline: Validate direct page link navigation
	  When I click the "<link_text>" link
	  Then I should be navigated to "<url_value>"
	  Then I should see the page title "<page_title>"
	Examples:
	  | link_text | url_value | page_title |
	{direct_links_rows}
	Scenario Outline: Validate dropdown link navigation
	  When I open the "<dropdown_name>" menu
	  And I select the "<link_text>" link under group "<group_name>"
	  Then I should be navigated to "<url_value>"
	  And I should see the page title "<page_title>"
	Examples:
	  | dropdown_name | group_name | link_text | url_value | page_title |
	{dropdown_links_rows}
	"""
	direct_rows = []
	for link in direct_links_data:
		# Sanitize data for Gherkin table
		link_text = link['link_text'].replace('|', '/')
		url_value = link['url_value']
		page_title = link['page_title'].replace('|', '/')
		direct_rows.append(f"  | {link_text} | {url_value} | {page_title} |")
	dropdown_rows = []
	for link in dropdown_links_data:
		# Sanitize data for Gherkin table
		dropdown_name = link['dropdown_name'].replace('|', '/')
		group_name = link['group_name'].replace('|', '/')
		link_text = link['link_text'].replace('|', '/')
		url_value = link['url_value']
		page_title = link['page_title'].replace('|', '/')
		dropdown_rows.append(f"  | {dropdown_name} | {group_name} | {link_text} | {url_value} | {page_title} |")
	final_gherkin = gherkin_template.format(
		direct_links_rows='\n'.join(direct_rows),
		dropdown_links_rows='\n'.join(dropdown_rows)
	).strip()
	print(final_gherkin)

	# Cell 6
	await done(text=final_gherkin, success=True)

	await browser.stop()

if __name__ == '__main__':
	

	asyncio.run(main())
