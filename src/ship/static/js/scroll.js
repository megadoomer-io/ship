(function () {
    'use strict';

    window.initInfiniteScroll = function (config) {
        var container = document.querySelector(config.container);
        if (!container) return;

        var sentinel = document.createElement('div');
        sentinel.className = 'scroll-sentinel';
        container.parentNode.insertBefore(sentinel, container.nextSibling);

        var offset = config.initialCount;
        var loading = false;
        var exhausted = false;

        var observer = new IntersectionObserver(function (entries) {
            if (!entries[0].isIntersecting || loading || exhausted) return;

            loading = true;
            var url = config.url + '?offset=' + offset + '&limit=' + config.limit +
                (config.extraParams || '');

            fetch(url)
                .then(function (r) { return r.text(); })
                .then(function (html) {
                    if (!html.trim()) {
                        exhausted = true;
                        sentinel.remove();
                        return;
                    }
                    container.insertAdjacentHTML('beforeend', html);
                    offset += config.limit;
                    loading = false;
                })
                .catch(function () { loading = false; });
        }, { rootMargin: '200px' });

        observer.observe(sentinel);
    };
})();
