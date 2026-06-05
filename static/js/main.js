// Tamipee Integrated Farms — Main JS

document.addEventListener('DOMContentLoaded', function () {
    const body = document.body;
    const feedbackHost = document.getElementById('siteFeedback');

    // ── Persist dismissed announcements across page loads ────────
    (function () {
        const dismissed = JSON.parse(sessionStorage.getItem('dismissedAnns') || '[]');

        document.querySelectorAll('#siteAnnouncementBar [data-ann-id]').forEach(function (el) {
            const id = el.dataset.annId;
            if (dismissed.includes(id)) {
                el.remove();
                return;
            }
            el.addEventListener('closed.bs.alert', function () {
                const current = JSON.parse(sessionStorage.getItem('dismissedAnns') || '[]');
                if (!current.includes(id)) {
                    current.push(id);
                    sessionStorage.setItem('dismissedAnns', JSON.stringify(current));
                }
                const bar = document.getElementById('siteAnnouncementBar');
                if (bar && !bar.querySelector('[data-ann-id]')) {
                    bar.remove();
                }
            });
        });
    }());

    const updateCartBadge = function (count) {
        const badge = document.getElementById('cartItemCountBadge');
        if (!badge || typeof count === 'undefined' || count === null) {
            return;
        }

        badge.textContent = String(count);
    };

    const showFeedbackToast = function (message, level) {
        if (!feedbackHost || !message) {
            return;
        }

        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-' + (level || 'success') + ' border-0';
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        toast.setAttribute('aria-atomic', 'true');
        toast.innerHTML = [
            '<div class="d-flex">',
            '  <div class="toast-body">' + message + '</div>',
            '  <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>',
            '</div>'
        ].join('');

        feedbackHost.appendChild(toast);
        const toastInstance = bootstrap.Toast.getOrCreateInstance(toast, { delay: 2600 });
        toast.addEventListener('hidden.bs.toast', function () {
            toast.remove();
        });
        toastInstance.show();
    };

    const submitAddToCart = function (form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton && submitButton.disabled) {
            return;
        }

        const formData = new FormData(form);
        if (submitButton) {
            submitButton.disabled = true;
        }

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            body: formData,
            credentials: 'same-origin',
        })
            .then(function (response) {
                return response.json().catch(function () {
                    return {};
                }).then(function (data) {
                    return { ok: response.ok, status: response.status, data: data };
                });
            })
            .then(function (result) {
                if (result.status === 401 && result.data.login_url) {
                    window.location.href = result.data.login_url;
                    return;
                }

                if (typeof result.data.cart_item_count !== 'undefined') {
                    updateCartBadge(result.data.cart_item_count);
                }

                showFeedbackToast(
                    result.data.message || (result.ok ? 'Item added to cart.' : 'Could not add item to cart.'),
                    result.ok ? 'success' : 'danger'
                );
            })
            .catch(function () {
                showFeedbackToast('Could not add item to cart right now. Please try again.', 'danger');
            })
            .finally(function () {
                if (submitButton) {
                    submitButton.disabled = false;
                }
            });
    };

    const prepareResponsiveTables = function () {
        document.querySelectorAll('table.table').forEach(function (table) {
            if (table.dataset.mobileStackReady === '1') {
                return;
            }

            const headerCells = table.querySelectorAll('thead th');
            if (!headerCells.length) {
                return;
            }

            const headers = Array.from(headerCells).map(function (th) {
                return th.textContent.trim() || 'Detail';
            });

            table.querySelectorAll('tbody tr').forEach(function (row) {
                row.querySelectorAll('td').forEach(function (cell, index) {
                    if (!cell.hasAttribute('data-label')) {
                        const label = headers[index] || 'Detail';
                        cell.setAttribute('data-label', label);
                    }
                });
            });

            table.classList.add('table-stack-mobile');
            table.dataset.mobileStackReady = '1';
        });
    };

    // ── Auto-dismiss alerts after 5 seconds ──────────────────────
    document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            bootstrap.Alert.getOrCreateInstance(alert).close();
        }, 5000);
    });

    // ── Scroll to top button ──────────────────────────────────────
    const scrollBtn = document.getElementById('scrollTop');
    if (scrollBtn) {
        window.addEventListener('scroll', function () {
            scrollBtn.classList.toggle('visible', window.scrollY > 320);
        });
        scrollBtn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ── Dashboard sidebar mobile toggle ──────────────────────────
    const sidebar = document.getElementById('dashboardSidebar');
    const mobileBtn = document.getElementById('sidebarMobileBtn');
    if (sidebar && mobileBtn) {
        mobileBtn.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
        // Close sidebar when clicking outside
        document.addEventListener('click', function (e) {
            if (sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !mobileBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ── Active nav link highlight (public navbar) ─────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar .nav-link').forEach(function (link) {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });

    // ── Improve mobile navbar behavior ─────────────────────────────
    const navbarCollapse = document.getElementById('navbarMain');
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarCollapse && navbarToggler) {
        const syncNavbarState = function () {
            const isOpen = navbarCollapse.classList.contains('show');
            navbarToggler.setAttribute('aria-expanded', String(isOpen));
            body.classList.toggle('nav-open', isOpen);
        };

        navbarCollapse.addEventListener('shown.bs.collapse', syncNavbarState);
        navbarCollapse.addEventListener('hidden.bs.collapse', syncNavbarState);

        navbarCollapse.querySelectorAll('a, button').forEach(function (item) {
            item.addEventListener('click', function (e) {
                if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
                    if (item.classList.contains('dropdown-toggle')) {
                        return;
                    }
                    if (item.classList.contains('dropdown-item')) {
                        return;
                    }
                    bootstrap.Collapse.getOrCreateInstance(navbarCollapse).hide();
                }
            });
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && navbarCollapse.classList.contains('show')) {
                bootstrap.Collapse.getOrCreateInstance(navbarCollapse).hide();
            }
        });

        syncNavbarState();
    }

    document.querySelectorAll('[data-add-to-cart-form]').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            submitAddToCart(form);
        });
    });

    prepareResponsiveTables();

});
