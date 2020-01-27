import pkgutil, json, requests, time

def json_file_to_dict(file_name):
    content = pkgutil.get_data(
        "oniAutorizacao", "resources/formularios/{}.json".format(file_name)
    )
    return dict(json.loads(content))

def raw_header_to_dict(raw):
    header = {}
    for i in raw.decode("utf-8").split(";"):
        item = [j.strip() for j in i.split("=")]
        if len(item) == 2:
            header[item[0]] = item[1]
    return header

def get_all_inputs_from_response(response):
    inputs = response.selector.xpath("//input")
    result = {}
    for i in inputs:
        result[i.xpath("@name").get()] = i.xpath("@value").get()
    return result

def str_to_json(json_string):
    if isinstance(json_string, str):
        try:
            return json.loads(json_string)
        except:
            return {}
    elif isinstance(json_string, dict):
        return json_string
    else:
        return {}

def save_pdf_from_url(url):
    response = requests.get(url, stream=True)
    temp_file_name = hash(time.time())
    anexo_path = "oniAutorizacao/resources/anexos/%d.pdf" % temp_file_name
    with open(anexo_path, "wb") as anexo:
        anexo.write(response.content)
    return anexo_path
