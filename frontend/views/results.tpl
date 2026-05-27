% rebase('base', email=email)

<h2 class="search-results-title">Search Results for "{{q}}"</h2>

<form method="post" action="/search" class="row search-row">
  <div class="search-box">
    <input
      id="search-input"
      class="search-input"
      type="text"
      name="q"
      value="{{q}}"
      placeholder="Search term"
      autocomplete="off"
      required
    >
    <ul id="suggestions" class="suggestions"></ul>
  </div>
  <button>Search</button>
</form>

% if not results:
  <p>No results found for "{{q}}".</p>
% else:
  <div class="results-list">
    % for r in results:
      <div class="result-card">
        <a href="{{r['url']}}" target="_blank" class="result-title">
          {{r['title']}}
        </a>

        <div class="result-url">
          {{r['display_url']}}
        </div>

        % if r['snippet']:
          <div class="result-snippet">
            {{r['snippet']}}
          </div>
        % end

        <div class="pagerank">
          PageRank: {{r['pagerank']}}
        </div>
      </div>
    % end
  </div>

  <div class="pagination">
    % if has_prev:
      <a href="/search?q={{q}}&page={{page-1}}" class="page-nav page-prev">
        ‹ Previous
      </a>
    % end

    % for p in pages:
      % if p == page:
        <span class="page-num current">{{p}}</span>
      % else:
        <a href="/search?q={{q}}&page={{p}}" class="page-num">{{p}}</a>
      % end
    % end

    % if has_next:
      <a href="/search?q={{q}}&page={{page+1}}" class="page-nav page-next">
        Next ›
      </a>
    % end
  </div>
% end

<div class="back-box">
  <a href="/" class="back-btn">Back</a>
</div>
