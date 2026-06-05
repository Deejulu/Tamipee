// Dashboard JS — Tamipee Farms

document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('dashboardSidebar');
    const backdrop = document.getElementById('dashboardBackdrop');
    const body = document.body;

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

    const syncSidebarState = function (isOpen) {
        if (!sidebar || !sidebarToggle || !backdrop) {
            return;
        }

        sidebar.classList.toggle('open', isOpen);
        body.classList.toggle('dashboard-nav-open', isOpen);
        sidebarToggle.setAttribute('aria-expanded', String(isOpen));
        backdrop.hidden = !isOpen;
    };

    if (sidebarToggle && sidebar && backdrop) {
        sidebarToggle.addEventListener('click', function () {
            syncSidebarState(!sidebar.classList.contains('open'));
        });

        backdrop.addEventListener('click', function () {
            syncSidebarState(false);
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && sidebar.classList.contains('open')) {
                syncSidebarState(false);
            }
        });

        sidebar.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                if (window.innerWidth < 992) {
                    syncSidebarState(false);
                }
            });
        });

        window.addEventListener('resize', function () {
            if (window.innerWidth >= 992) {
                syncSidebarState(false);
            }
        });
    }

    // Auto-dismiss alerts
    document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    prepareResponsiveTables();
});
