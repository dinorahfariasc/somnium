# import scrapy
# from sonhos.items import SonhoItem
# import string
# import re

# class LivroDoSonhoSpider(scrapy.Spider):
#     name = "livrodosonho"
#     allowed_domains = ["livrodosonho.com"]
#     start_urls = [
#         f"https://www.livrodosonho.com/significado-dos-sonhos/significado-dos-sonhos-letra-{letra}"
#         for letra in string.ascii_lowercase
#     ]

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.contador_por_letra = {}

#     def parse(self, response):
#         inicial = response.url.split("-")[-1]
#         links = response.css("ul.button-group li a::attr(href)").getall()

#         for href in links:
#             if href.startswith("//"):
#                 href = "https:" + href
#             elif href.startswith("/"):
#                 href = "https://www.livrodosonho.com" + href
#             yield scrapy.Request(
#                 href,
#                 callback=self.parse_sonho,
#                 meta={'inicial': inicial, 'url': href}
#             )

#     def parse_sonho(self, response):
#         item = SonhoItem()
#         letra = response.meta['inicial']
#         item['inicial'] = letra
#         item['url'] = response.meta['url']
#         item['sonho'] = response.css("h1.entry-title::text").get(default="").strip().lower()

#         paragrafos = response.css("div.post-entry p::text").getall()

#         significado = []
#         loteria_buffer = []
#         coletando_loterias = False

#         item['bicho'] = item['grupo'] = item['dezena'] = item['centena'] = item['milhar'] = None
#         item['quina'] = item['megasena'] = item['lotofacil'] = item['timemania'] = None

#         for p in paragrafos:
#             p = p.strip()
#             if not p:
#                 continue

#             if "Acredite na sua sorte" in p:
#                 coletando_loterias = True
#                 continue

#             if coletando_loterias:
#                 loteria_buffer.append(p)
#             else:
#                 significado.append(p)

#             if "BICHO" in p:
#                 partes = p.split("|")
#                 for parte in partes:
#                     if "BICHO" in parte:
#                         item["bicho"] = parte.split("=")[1].strip()
#                     elif "GRUPO" in parte:
#                         item["grupo"] = parte.split("=")[1].strip()
#                     elif "DEZENA" in parte:
#                         item["dezena"] = parte.split("=")[1].strip()
#                     elif "CENTENA" in parte:
#                         item["centena"] = parte.split("=")[1].strip()
#                     elif "MILHAR" in parte:
#                         item["milhar"] = parte.split("=")[1].strip()

#         item['significado'] = "\n".join(significado).strip()

#         loteria_ordem = ["quina", "megasena", "lotofacil", "timemania"]
#         loteria_numeros = [linha.strip(" :–-") for linha in loteria_buffer if re.search(r"\d", linha)]

#         for i, nome in enumerate(loteria_ordem):
#             if i < len(loteria_numeros):
#                 numeros = re.findall(r"\d{2}", loteria_numeros[i])
#                 item[nome] = ";".join(numeros)

#         self.contador_por_letra[letra] = self.contador_por_letra.get(letra, 0) + 1
#         yield item

#     def closed(self, reason):
#         print("\n📊 Resumo da coleta por letra:")
#         for letra, total in sorted(self.contador_por_letra.items()):
#             print(f"Letra {letra.upper()}: {total} sonhos coletados.")


# versão 2 apenas significados
import scrapy
import string
# from sonhos.items import SonhoItem # Descomente esta linha no seu projeto

# Definição de item para teste, substitua pela sua
class SonhoItem(scrapy.Item):
    inicial = scrapy.Field()
    sonho = scrapy.Field()
    significado = scrapy.Field()

class LivroDoSonhoSpider(scrapy.Spider):
    name = "livrodosonho"
    allowed_domains = ["livrodosonho.com"]
    start_urls = [
        f"https://www.livrodosonho.com/significado-dos-sonhos/significado-dos-sonhos-letra-{letra}"
        for letra in string.ascii_lowercase
    ]

    def parse(self, response):
        inicial = response.url.split("-")[-1]
        links = response.css("ul.button-group li a::attr(href)").getall()

        for href in links:
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = "https://www.livrodosonho.com" + href
            yield scrapy.Request(
                href,
                callback=self.parse_sonho,
                meta={'inicial': inicial}
            )

    def parse_sonho(self, response):
        item = SonhoItem()
        item['inicial'] = response.meta['inicial']
        item['sonho'] = response.css("h1.entry-title::text").get(default="").strip().lower()

        # 1. Seletor ATUALIZADO para ignorar tags <script> e <style>
        text_nodes = response.css("div.post-entry *:not(script):not(style)::text").getall()

        significado_parts = []
        for text in text_nodes:
            clean_text = text.strip()

            if "jogo do bicho" in clean_text.lower() or "acredite na sua sorte" in clean_text.lower():
                break

            if clean_text and "significado sonhar com" not in clean_text.lower():
                significado_parts.append(clean_text)

        # Junta e limpa o resultado final
        significado_final = ' '.join(significado_parts).strip()
        
        # Opcional: recria quebras de linha para melhor formatação em alguns casos
        # Adicione mais substituições se encontrar outros padrões
        significado_final = significado_final.replace('Ver um pregando:', '\nVer um pregando:')

        item['significado'] = significado_final

        yield item

    def closed(self, reason):
        stats = self.crawler.stats.get_stats()
        item_count = stats.get('item_scraped_count', 0)
        print(f"\n\n📊 Coleta finalizada! Total de {item_count} sonhos coletados.")
        print(f"Motivo do encerramento: {reason}")