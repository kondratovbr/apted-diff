from bs4 import BeautifulSoup, NavigableString

def main():
    html = """
    <html>
        <head>
            <title>Sample Page</title>
        </head>
        <body>
            <h1>Hello, <span>World!</span></h1>
            <p>This is <b>hardcoded</b> HTML content.</p>
            <div>
                <ul>
                    <li>Nested</li>
                    <li>List</li>
                    <li>Items</li>
                </ul>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    # Extract each piece of text from the HTML as a list
    texts = [string.strip() for string in soup.stripped_strings]
    print(texts)

    text_nodes = []
    # Recursively gather all text nodes
    def get_all_text_nodes(soup_elem):
        for elem in soup_elem.descendants:
            if isinstance(elem, NavigableString) and elem.strip() != "":
                print(type(elem))
                text_nodes.append(elem)
    get_all_text_nodes(soup)
    print(text_nodes)

if __name__ == "__main__":
    main()