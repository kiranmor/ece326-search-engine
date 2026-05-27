% rebase('base', email=email)

% if email:
  <form method="post" action="/search" class="row">
    <div class="search-box">
      <input
        id="search-input"
        class="search-input"
        type="text"
        name="q"
        placeholder="Search term"
        autocomplete="off"
        required
      >
      <ul id="suggestions" class="suggestions"></ul>
    </div>
    <button>Search</button>
  </form>

  <div class="recent-searches">
    <h3>Your recent searches</h3>
    % if qs:
      <div class="recent-tags">
        % for x in qs:
          <a class="recent-tag" href="/search?q={{x}}">{{x}}</a>
        % end
      </div>
    % else:
      <p class="recent-empty">(No history yet)</p>
    % end
  </div>

% else:
  <p class="anon-label">Anonymous mode</p>
  <form method="post" action="/search" class="row">
    <div class="search-box">
      <input
        id="search-input"
        class="search-input"
        type="text"
        name="q"
        placeholder="Search term"
        autocomplete="off"
        required
      >
      <ul id="suggestions" class="suggestions"></ul>
    </div>
    <button>Search</button>
  </form>

  <p style="margin-top: 1rem;">
    <a href="/login">
      <button type="button">Sign in with Google</button>
    </a>
  </p>
% end
