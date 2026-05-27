<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Meowgle</title>
    <link rel="icon" href="/static/img/design.png" type="image/png">
    <link rel="stylesheet" href="/static/main.css">
  </head>

  <body>
    <header class="meow-header">
      % if email:
        <!-- Avatar button -->
        <div class="account-avatar" id="account-avatar">
          <div class="avatar-initial">{{email[0].upper()}}</div>
        </div>

        <!-- Dropdown account menu -->
        <div class="account-menu" id="account-menu">
          <div class="account-menu-header">
            <div class="account-menu-title">Meowgle Account</div>
            <div class="account-menu-email">{{email}}</div>
          </div>
          <div class="account-menu-actions">
            <form method="post" action="/logout">
              <button type="submit" class="logout-btn-wide">Sign out</button>
            </form>
          </div>
        </div>
      % end

      <!-- Center branding: logo + Meowgle -->
      <div class="branding">
        <img src="/static/img/logo-png.png" class="logo" alt="Meowgle Logo">
        <h1 class="meow-title">Meowgle🔍</h1>
      </div>
    </header>

    <main>
      {{!base}}
    </main>

    <!-- Avatar menu JS -->
    <script>
      (function () {
        const avatar = document.getElementById('account-avatar');
        const menu   = document.getElementById('account-menu');
        if (!avatar || !menu) return;

        function openMenu() {
          menu.classList.add('open');
        }
        function closeMenu() {
          menu.classList.remove('open');
        }

        avatar.addEventListener('click', function (e) {
          e.stopPropagation();
          if (menu.classList.contains('open')) {
            closeMenu();
          } else {
            openMenu();
          }
        });

        document.addEventListener('click', function (e) {
          if (!menu.contains(e.target) && !avatar.contains(e.target)) {
            closeMenu();
          }
        });

        document.addEventListener('keydown', function (e) {
          if (e.key === 'Escape') {
            closeMenu();
          }
        });
      })();
    </script>

    <!-- Shared autocomplete / suggestion JS (home + results 共用) -->
    <script>
      (function () {
        const input    = document.getElementById('search-input');
        const dropdown = document.getElementById('suggestions');
        if (!input || !dropdown) return;

        let debounceTimer   = null;
        let userTyped       = "";
        let inlineSuggestion = "";
        let suggestions     = [];
        let lastKey         = null;

        function clearDropdown() {
          dropdown.innerHTML      = "";
          dropdown.style.display  = "none";
          suggestions             = [];
          inlineSuggestion        = "";
        }

        function renderDropdown(list) {
          if (!Array.isArray(list) || list.length === 0) {
            clearDropdown();
            return;
          }
          dropdown.innerHTML = "";
          list.forEach(function (item) {
            const li = document.createElement('li');
            li.textContent = item;
            li.addEventListener('mousedown', function (e) {
              // Use mousedown so the click does not blur the input first
              e.preventDefault();
              input.value = item;
              userTyped   = item;
              input.setSelectionRange(item.length, item.length);
              clearDropdown();
            });
            dropdown.appendChild(li);
          });
          dropdown.style.display = "block";
        }

        function applyInlineCompletion(prefix, suggestion) {
          if (!suggestion) return;
          if (!suggestion.toLowerCase().startsWith(prefix.toLowerCase())) return;
          if (suggestion.length <= prefix.length) return;

          input.value = suggestion;
          input.setSelectionRange(prefix.length, suggestion.length);
        }

        input.addEventListener('keydown', function (e) {
          lastKey = e.key;

          // Accept inline suggestion with Tab / ArrowRight
          if ((e.key === 'Tab' || e.key === 'ArrowRight') && inlineSuggestion) {
            const start = input.selectionStart;
            const end   = input.selectionEnd;
            if (start !== end) {
              e.preventDefault();
              input.value = inlineSuggestion;
              userTyped   = inlineSuggestion;
              input.setSelectionRange(inlineSuggestion.length, inlineSuggestion.length);
            }
          }

          // Escape cancels suggestion
          if (e.key === 'Escape') {
            e.preventDefault();
            input.value = userTyped;
            input.setSelectionRange(userTyped.length, userTyped.length);
            clearDropdown();
          }
        });

        input.addEventListener('input', function () {
          const caret = input.selectionStart;
          const raw   = input.value;
          userTyped   = raw.slice(0, caret);

          clearTimeout(debounceTimer);

          if (!userTyped.trim()) {
            clearDropdown();
            lastKey = null;
            return;
          }

          const isDelete = (lastKey === 'Backspace' || lastKey === 'Delete');

          debounceTimer = setTimeout(function () {
            fetch('/suggest?q=' + encodeURIComponent(userTyped))
              .then(res => res.json())
              .then(list => {
                suggestions      = Array.isArray(list) ? list : [];
                inlineSuggestion = suggestions[0] || "";
                renderDropdown(suggestions);

                if (inlineSuggestion && !isDelete) {
                  // Normal typing: show inline completion
                  applyInlineCompletion(userTyped, inlineSuggestion);
                } else {
                  // Deleting: keep user's text, do not inline-complete
                  input.value = userTyped;
                  input.setSelectionRange(userTyped.length, userTyped.length);
                }
              })
              .catch(err => {
                console.error('suggest error:', err);
                clearDropdown();
              })
              .finally(() => {
                lastKey = null;
              });
          }, 150);
        });

        document.addEventListener('click', function (e) {
          if (e.target !== input && !dropdown.contains(e.target)) {
            clearDropdown();
          }
        });
      })();
    </script>

  </body>
</html>
