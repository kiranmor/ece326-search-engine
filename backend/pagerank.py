from crawler import crawler
from storage import save_to_db

class webcrawl:
    def __init__(self, urls_file):
        self.bot = crawler(None, urls_file)
    
    def run_crawl(self, depth=1):
        self.bot.crawl(depth=depth)
        return self.bot.get_link_graph()

class pagerank:
    def __init__(self, graph, damping_factor=0.85, steps=100):
        self.graph = graph
        self.damping_factor = damping_factor
        self.steps = steps  
    
    def calculate(self):
        num_pages = len(self.graph)
        ranks = {page: 1 / num_pages for page in self.graph}
        
        for _ in range(self.steps):
            new_ranks = {}
            for page in self.graph:
                rank_sum = 0
                for other_page, links in self.graph.items():
                    if page in links:
                        rank_sum += ranks[other_page] / len(links)
                new_ranks[page] = (1 - self.damping_factor) / num_pages + self.damping_factor * rank_sum
            ranks = new_ranks
        
        return ranks

class results:
    def save_results(self, bot, ranks):
        save_to_db(bot, ranks)


if __name__ == "__main__":
    crawler_obj = webcrawl("urls.txt")
    link_graph = crawler_obj.run_crawl(depth=1)
    rank = pagerank(link_graph,steps=50).calculate()
    results().save_results(crawler_obj.bot, rank)