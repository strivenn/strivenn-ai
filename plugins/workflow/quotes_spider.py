import scrapy
class QuotesSpider(scrapy.Spider):
    name = 'quotes'

    def __init__(self, start_url=None, *args, **kwargs):
        super(QuotesSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []

    def parse(self, response):
        # Extract the title
        title = response.xpath('//h1//text()').get()
        title = title.strip() if title else ""

        # Initialize structured data
        text_data = {
            "Title": title,
            "Content": ""
        }

        # Extract elements
        xpath_expressions = [
            '//main//h2|//main//h3|//main//h4|//main//h5|//main//h6|//main//p',
            '//h2|//h3|//h4|//h5|//h6|//p'
        ]

        elements = None
        for xpath in xpath_expressions:
            elements = response.xpath(xpath)
            if elements:
                break

        current_subtitle = None

        for element in elements:
            item = {}
            tag = element.root.tag

            if tag in ['h2', 'h3', 'h4', 'h5', 'h6']:
                # This is a subtitle
                current_subtitle = element.xpath('.//text()').get().strip()
                text_data["Content"] += f"Subtitle: {current_subtitle}\n"

            elif tag == 'p':
                # This is a paragraph
                paragraph_text = element.xpath('.//text()').get()
                if paragraph_text:
                    paragraph_text = paragraph_text.strip()
                    text_data["Content"] += f"P: {paragraph_text}\n"

            elif tag == 'div':
                # Handle divs with potential nested content
                div_header = element.xpath('.//h2|.//h3|.//h4|.//h5|.//h6').xpath('.//text()').get()
                if div_header:
                    div_header = div_header.strip()
                    text_data["Content"] += f"Div: {div_header}\n"
                # Extract all paragraphs inside the div
                p_elements = element.xpath('.//p')
                for p_element in p_elements:
                    paragraph_text = p_element.xpath('.//text()').get()
                    if paragraph_text:
                        paragraph_text = paragraph_text.strip()
                        text_data["Content"] += f"P: {paragraph_text}\n"

        # Yield the text data in the specified JSON format
        yield text_data