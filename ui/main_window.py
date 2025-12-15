"""
LinkedIn Job Scraper - Main Window
Main application window with professional UI layout
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QStatusBar, QSplitter, QLineEdit,
    QComboBox, QPushButton, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QTextEdit,
    QScrollArea, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QDesktopServices

import config
from data import JobDataManager
from scraping.linkedin_scraper import LinkedInScraper


class ScrapingWorker(QThread):
    """Worker thread for scraping operations to prevent UI blocking"""
    
    # Signals for communication with main thread
    progress_update = pyqtSignal(str)  # Status message
    progress_percentage = pyqtSignal(int)  # Progress percentage (0-100)
    jobs_found = pyqtSignal(list)     # List of jobs found
    scraping_finished = pyqtSignal(bool, str)  # Success status and message
    page_progress = pyqtSignal(int, int)  # Current page, total pages
    
    def __init__(self, job_title, location, job_type, experience_level, max_pages=3):
        super().__init__()
        self.job_title = job_title
        self.location = location
        self.job_type = job_type
        self.experience_level = experience_level
        self.max_pages = max_pages
        self.scraper = None
        
    def run(self):
        """Run the scraping operation in background thread"""
        try:
            # Phase 1: Initialization (0-10%)
            self.progress_update.emit("Initializing web scraper...")
            self.progress_percentage.emit(5)
            
            # Create scraper instance
            self.scraper = LinkedInScraper(headless=True)
            
            # Phase 2: Connection (10-20%)
            self.progress_update.emit("Connecting to LinkedIn...")
            self.progress_percentage.emit(15)
            
            # Phase 3: Navigation (20-30%)
            self.progress_update.emit("Navigating to LinkedIn jobs page...")
            self.progress_percentage.emit(25)
            
            # Phase 4: Search setup (30-40%)
            search_params = []
            if self.job_title:
                search_params.append(f"'{self.job_title}'")
            if self.location:
                search_params.append(f"in {self.location}")
            if self.job_type != "All":
                search_params.append(f"({self.job_type})")
            
            search_description = " ".join(search_params) if search_params else "all jobs"
            self.progress_update.emit(f"Searching for {search_description}...")
            self.progress_percentage.emit(35)
            
            # Phase 5: Actual scraping (40-90%)
            jobs = self.scraper.search_jobs(
                job_title=self.job_title,
                location=self.location,
                job_type=self.job_type,
                experience_level=self.experience_level,
                max_pages=self.max_pages
            )
            
            # Phase 6: Processing results (90-100%)
            if jobs:
                self.progress_update.emit(f"Processing {len(jobs)} job listings...")
                self.progress_percentage.emit(95)
                self.jobs_found.emit(jobs)
                self.progress_percentage.emit(100)
                self.scraping_finished.emit(True, f"Successfully found {len(jobs)} jobs")
            else:
                self.progress_percentage.emit(100)
                self.scraping_finished.emit(False, "No jobs found matching your criteria. Try different search terms or check your internet connection.")
                
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            print(f"Scraping error details: {error_msg}")
            self.progress_percentage.emit(0)
            self.scraping_finished.emit(False, error_msg)
        finally:
            # Clean up scraper resources
            if self.scraper:
                try:
                    self.scraper.cleanup()
                except Exception as cleanup_error:
                    print(f"Error during cleanup: {cleanup_error}")


class MainWindow(QMainWindow):
    """Main application window for LinkedIn Job Scraper"""
    
    def __init__(self):
        super().__init__()
        # Initialize data manager
        self.data_manager = JobDataManager()
        self.scraping_worker = None
        self.setup_window_properties()
        self.setup_ui()
        self.apply_styling()
        
    def setup_window_properties(self):
        """Configure basic window properties"""
        # Set window title
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        
        # Set window size and constraints
        self.resize(config.DEFAULT_WINDOW_WIDTH, config.DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT)
        
        # Center window on screen
        self.center_on_screen()
        
    def center_on_screen(self):
        """Center the window on the screen"""
        screen = self.screen().availableGeometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        self.move(window.topLeft())
        
    def setup_ui(self):
        """Set up the main user interface layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create and add header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Create main content area with splitter
        content_splitter = QSplitter(Qt.Vertical)
        
        # Create search panel
        search_panel = self.create_search_panel()
        content_splitter.addWidget(search_panel)
        
        # Create results area
        results_area = self.create_results_area()
        content_splitter.addWidget(results_area)
        
        # Set splitter proportions (search panel smaller, results area larger)
        content_splitter.setSizes([200, 600])
        content_splitter.setCollapsible(0, False)  # Don't allow search panel to collapse
        content_splitter.setCollapsible(1, False)  # Don't allow results area to collapse
        
        main_layout.addWidget(content_splitter)
        
        # Create and set status bar
        self.setup_status_bar()
        
    def connect_search_signals(self):
        """Connect search interface signals to handler methods"""
        self.search_button.clicked.connect(self.handle_search)
        self.clear_button.clicked.connect(self.handle_clear_filters)
        
    def handle_search(self):
        """Handle search button click"""
        # Get search parameters
        job_title = self.job_title_input.text().strip()
        location = self.location_input.text().strip()
        job_type = self.job_type_combo.currentText()
        experience_level = self.experience_combo.currentText()
        
        # Basic validation
        if not job_title and not location:
            self.statusBar().showMessage("Please enter a job title or location to search")
            return
            
        # Update status bar
        search_params = []
        if job_title:
            search_params.append(f"Title: {job_title}")
        if location:
            search_params.append(f"Location: {location}")
        if job_type != "All":
            search_params.append(f"Type: {job_type}")
        if experience_level != "All":
            search_params.append(f"Level: {experience_level}")
            
        status_message = f"Searching for jobs - {', '.join(search_params)}"
        self.statusBar().showMessage(status_message)
        
        # Start scraping in background thread
        self.start_scraping(job_title, location, job_type, experience_level)
    
    def start_scraping(self, job_title, location, job_type, experience_level):
        """Start the scraping process in a background thread"""
        # Disable search button and show progress
        self.search_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Preparing to search...")
        self.clear_results_table()
        
        # Create and start worker thread
        self.scraping_worker = ScrapingWorker(
            job_title=job_title,
            location=location, 
            job_type=job_type,
            experience_level=experience_level,
            max_pages=3
        )
        
        # Connect worker signals
        self.scraping_worker.progress_update.connect(self.update_scraping_progress)
        self.scraping_worker.progress_percentage.connect(self.update_progress_percentage)
        self.scraping_worker.jobs_found.connect(self.handle_jobs_found)
        self.scraping_worker.scraping_finished.connect(self.handle_scraping_finished)
        
        # Start the worker
        self.scraping_worker.start()
    
    def update_scraping_progress(self, message):
        """Update the progress message during scraping"""
        self.statusBar().showMessage(message)
        self.progress_label.setText(message)
    
    def update_progress_percentage(self, percentage):
        """Update the progress bar percentage"""
        self.progress_bar.setValue(percentage)
    
    def handle_jobs_found(self, jobs):
        """Handle jobs found during scraping"""
        if jobs:
            self.populate_results_table(jobs)
            self.statusBar().showMessage(f"Found {len(jobs)} jobs")
    
    def handle_scraping_finished(self, success, message):
        """Handle scraping completion"""
        # Re-enable search button and hide progress
        self.search_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Update status bar with final message
        self.statusBar().showMessage(message)
        
        # Show message box for important notifications
        if not success:
            QMessageBox.warning(self, "Scraping Error", 
                              f"Failed to scrape jobs:\n\n{message}\n\n"
                              "This could be due to:\n"
                              "• Network connectivity issues\n"
                              "• LinkedIn blocking automated access\n"
                              "• Changes to LinkedIn's website structure\n\n"
                              "Please try again in a few minutes.")
        elif success and ("0 jobs" in message or "No jobs found" in message):
            QMessageBox.information(self, "No Results", 
                                  "No jobs found matching your search criteria.\n\n"
                                  "Try:\n"
                                  "• Using different keywords\n"
                                  "• Expanding your location search\n"
                                  "• Removing some filters\n"
                                  "• Checking your spelling")
        elif success:
            # Show success message briefly in status bar
            job_count = message.split()[-2] if "found" in message else "some"
            self.statusBar().showMessage(f"✓ Successfully loaded {job_count} jobs", 5000)
        
        # Clean up worker
        if self.scraping_worker:
            self.scraping_worker.deleteLater()
            self.scraping_worker = None
        
    def handle_clear_filters(self):
        """Handle clear filters button click"""
        # Reset all input fields to default values
        self.job_title_input.clear()
        self.location_input.clear()
        self.job_type_combo.setCurrentIndex(0)  # Set to "All"
        self.experience_combo.setCurrentIndex(0)  # Set to "All"
        
        # Update status bar
        self.statusBar().showMessage("Filters cleared - Ready to search LinkedIn jobs")
        
    def handle_results_search(self):
        """Handle search within results"""
        search_term = self.results_search_input.text().strip()
        self.apply_results_filters()
        
    def handle_results_filter(self):
        """Handle status filter change"""
        self.apply_results_filters()
        
    def handle_clear_results_filters(self):
        """Handle clear results filters button click"""
        self.results_search_input.clear()
        self.status_filter_combo.setCurrentIndex(0)  # Set to "All Statuses"
        self.apply_results_filters()
        self.statusBar().showMessage("Results filters cleared")
        
    def apply_results_filters(self):
        """Apply current filters and search to the results table"""
        if self.data_manager.get_job_count() == 0:
            return
            
        # Get current filter values
        search_term = self.results_search_input.text().strip()
        status_filter = self.status_filter_combo.currentText()
        
        # Start with all jobs
        filtered_jobs = self.data_manager.get_all_jobs()
        
        # Apply search filter
        if search_term:
            filtered_jobs = [job for job in filtered_jobs 
                           if (search_term.lower() in job.get('title', '').lower() or
                               search_term.lower() in job.get('company', '').lower() or
                               search_term.lower() in job.get('description', '').lower())]
        
        # Apply status filter
        if status_filter != "All Statuses":
            filtered_jobs = [job for job in filtered_jobs 
                           if job.get('status') == status_filter]
        
        # Update the table with filtered results
        self.update_results_table_with_filtered_jobs(filtered_jobs)
        
        # Update status bar
        total_jobs = self.data_manager.get_job_count()
        filtered_count = len(filtered_jobs)
        
        if search_term and status_filter != "All Statuses":
            self.statusBar().showMessage(f"Showing {filtered_count} of {total_jobs} jobs (filtered by search and status)")
        elif search_term:
            self.statusBar().showMessage(f"Showing {filtered_count} of {total_jobs} jobs (filtered by search)")
        elif status_filter != "All Statuses":
            self.statusBar().showMessage(f"Showing {filtered_count} of {total_jobs} jobs (filtered by status)")
        else:
            self.statusBar().showMessage(f"Showing all {total_jobs} jobs")
            
    def update_results_table_with_filtered_jobs(self, filtered_jobs):
        """Update the results table to show only filtered jobs"""
        # Clear the table
        self.results_table.setRowCount(0)
        if hasattr(self, 'row_to_job_id'):
            self.row_to_job_id.clear()
        
        # Add filtered jobs to the table
        for job_data in filtered_jobs:
            self.add_job_to_table_without_data_manager(job_data)
            
    def add_job_to_table_without_data_manager(self, job_data):
        """Add a job to the table without adding to data manager (for filtering)"""
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        
        # Add job data to columns
        self.results_table.setItem(row_position, 0, QTableWidgetItem(job_data.get('title', '')))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(job_data.get('company', '')))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(job_data.get('location', '')))
        self.results_table.setItem(row_position, 3, QTableWidgetItem(job_data.get('posted_date', '')))
        
        # Create status dropdown
        status_combo = QComboBox()
        status_combo.setObjectName("statusCombo")
        status_combo.addItems(self.data_manager.status_options)
        
        # Set current status
        current_status = job_data.get('status', 'Not Reviewed')
        status_index = status_combo.findText(current_status)
        if status_index >= 0:
            status_combo.setCurrentIndex(status_index)
        
        # Connect status change signal to data manager
        job_id = job_data.get('id')
        status_combo.currentTextChanged.connect(
            lambda status, job_id=job_id: self.handle_status_change_with_refresh(job_id, status)
        )
        
        # Add status dropdown to table
        self.results_table.setCellWidget(row_position, 4, status_combo)
        
        # Store row to job_id mapping for table operations
        if not hasattr(self, 'row_to_job_id'):
            self.row_to_job_id = {}
        self.row_to_job_id[row_position] = job_id
        
    def handle_status_change_with_refresh(self, job_id, new_status):
        """Handle status change and refresh filters if needed"""
        # Update status in data manager
        if self.data_manager.update_job_status(job_id, new_status):
            # Get updated job data for feedback
            job_data = self.data_manager.get_job(job_id)
            if job_data:
                job_title = job_data.get('title', 'Job')
                self.statusBar().showMessage(f"Status updated: {job_title} - {new_status}")
            else:
                self.statusBar().showMessage(f"Status updated to: {new_status}")
                
            # Refresh the filtered view if filters are active
            if (self.results_search_input.text().strip() or 
                self.status_filter_combo.currentText() != "All Statuses"):
                self.apply_results_filters()
        else:
            self.statusBar().showMessage("Failed to update job status")
        
    def create_header(self):
        """Create the application header with title and branding"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Application title
        title_label = QLabel(config.APP_NAME)
        title_label.setObjectName("titleLabel")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title_label.setFont(title_font)
        
        # Subtitle
        subtitle_label = QLabel("Professional LinkedIn Job Search Tool")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_font = QFont("Segoe UI", 10)
        subtitle_label.setFont(subtitle_font)
        
        # Title container
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()  # Push content to the left
        
        return header_frame
        
    def create_search_panel(self):
        """Create the search input panel"""
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_frame.setMinimumHeight(200)
        
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(20, 15, 20, 15)
        
        # Search panel title
        search_title = QLabel("Job Search")
        search_title.setObjectName("sectionTitle")
        search_title_font = QFont("Segoe UI", 12, QFont.Bold)
        search_title.setFont(search_title_font)
        
        search_layout.addWidget(search_title)
        
        # Create search form layout
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        
        # Job title input
        job_title_label = QLabel("Job Title:")
        job_title_label.setObjectName("inputLabel")
        self.job_title_input = QLineEdit()
        self.job_title_input.setObjectName("jobTitleInput")
        self.job_title_input.setPlaceholderText("e.g., Software Engineer, Data Analyst, Product Manager")
        
        # Location input
        location_label = QLabel("Location:")
        location_label.setObjectName("inputLabel")
        self.location_input = QLineEdit()
        self.location_input.setObjectName("locationInput")
        self.location_input.setPlaceholderText("e.g., New York, NY or Remote")
        
        # Job type filter dropdown
        job_type_label = QLabel("Job Type:")
        job_type_label.setObjectName("inputLabel")
        self.job_type_combo = QComboBox()
        self.job_type_combo.setObjectName("jobTypeCombo")
        self.job_type_combo.addItems([
            "All",
            "Full-time",
            "Part-time", 
            "Contract",
            "Internship"
        ])
        
        # Experience level filter dropdown
        experience_label = QLabel("Experience Level:")
        experience_label.setObjectName("inputLabel")
        self.experience_combo = QComboBox()
        self.experience_combo.setObjectName("experienceCombo")
        self.experience_combo.addItems([
            "All",
            "Entry",
            "Mid",
            "Senior",
            "Executive"
        ])
        
        # Add inputs to form layout
        form_layout.addWidget(job_title_label, 0, 0)
        form_layout.addWidget(self.job_title_input, 0, 1)
        form_layout.addWidget(location_label, 1, 0)
        form_layout.addWidget(self.location_input, 1, 1)
        form_layout.addWidget(job_type_label, 2, 0)
        form_layout.addWidget(self.job_type_combo, 2, 1)
        form_layout.addWidget(experience_label, 3, 0)
        form_layout.addWidget(self.experience_combo, 3, 1)
        
        # Set column stretch to make input fields expand
        form_layout.setColumnStretch(1, 1)
        
        search_layout.addLayout(form_layout)
        
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Search button
        self.search_button = QPushButton("Search Jobs")
        self.search_button.setObjectName("searchButton")
        self.search_button.setMinimumHeight(35)
        
        # Clear filters button
        self.clear_button = QPushButton("Clear Filters")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setMinimumHeight(35)
        
        # Add buttons to layout
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()  # Push buttons to the left
        
        search_layout.addLayout(button_layout)
        search_layout.addStretch()
        
        # Add progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)  # Percentage-based progress
        self.progress_bar.setValue(0)
        search_layout.addWidget(self.progress_bar)
        
        # Add progress label for detailed status
        self.progress_label = QLabel()
        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setVisible(False)
        self.progress_label.setWordWrap(True)
        search_layout.addWidget(self.progress_label)
        
        # Connect button signals to handler methods
        self.connect_search_signals()
        
        return search_frame
        
    def create_results_area(self):
        """Create the results display area"""
        results_frame = QFrame()
        results_frame.setObjectName("resultsFrame")
        
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(20, 15, 20, 15)
        
        # Results panel title
        results_title = QLabel("Job Results")
        results_title.setObjectName("sectionTitle")
        results_title_font = QFont("Segoe UI", 12, QFont.Bold)
        results_title.setFont(results_title_font)
        
        results_layout.addWidget(results_title)
        
        # Create results filtering panel
        filter_panel = self.create_results_filter_panel()
        results_layout.addWidget(filter_panel)
        
        # Create results table widget
        self.results_table = self.create_results_table()
        results_layout.addWidget(self.results_table)
        
        return results_frame
        
    def create_results_filter_panel(self):
        """Create the results filtering and search panel"""
        filter_frame = QFrame()
        filter_frame.setObjectName("resultsFilterFrame")
        filter_frame.setMaximumHeight(80)
        
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(15)
        
        # Search within results
        search_label = QLabel("Search Results:")
        search_label.setObjectName("filterLabel")
        search_font = QFont("Segoe UI", 10, QFont.Bold)
        search_label.setFont(search_font)
        
        self.results_search_input = QLineEdit()
        self.results_search_input.setObjectName("resultsSearchInput")
        self.results_search_input.setPlaceholderText("Search job titles, companies, or descriptions...")
        self.results_search_input.setMaximumWidth(300)
        self.results_search_input.textChanged.connect(self.handle_results_search)
        
        # Filter by status
        status_filter_label = QLabel("Status:")
        status_filter_label.setObjectName("filterLabel")
        status_filter_label.setFont(search_font)
        
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.setObjectName("statusFilterCombo")
        self.status_filter_combo.addItem("All Statuses")
        self.status_filter_combo.addItems(self.data_manager.status_options)
        self.status_filter_combo.setMaximumWidth(150)
        self.status_filter_combo.currentTextChanged.connect(self.handle_results_filter)
        
        # Clear filters button
        self.clear_results_filters_button = QPushButton("Clear Filters")
        self.clear_results_filters_button.setObjectName("clearResultsFiltersButton")
        self.clear_results_filters_button.setMaximumWidth(100)
        self.clear_results_filters_button.clicked.connect(self.handle_clear_results_filters)
        
        # Add widgets to layout
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.results_search_input)
        filter_layout.addWidget(status_filter_label)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addWidget(self.clear_results_filters_button)
        filter_layout.addStretch()  # Push everything to the left
        
        return filter_frame
        
    def create_results_table(self):
        """Create and configure the results table widget"""
        table = QTableWidget()
        table.setObjectName("resultsTable")
        
        # Set up columns
        columns = ["Job Title", "Company", "Location", "Posted Date", "Status"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # Configure table properties
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setSortingEnabled(True)
        table.setShowGrid(False)
        
        # Configure header
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        
        # Set column widths and resize modes
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Job Title - stretch to fill
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Company - fit content
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Location - fit content
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Posted Date - fit content
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Status - fixed width
        
        # Set minimum column widths
        table.setColumnWidth(1, 150)  # Company minimum width
        table.setColumnWidth(2, 120)  # Location minimum width
        table.setColumnWidth(3, 100)  # Posted Date minimum width
        table.setColumnWidth(4, 130)  # Status fixed width
        
        # Set minimum row height
        table.verticalHeader().setDefaultSectionSize(40)
        table.verticalHeader().setVisible(False)  # Hide row numbers
        
        # Set initial empty state message
        table.setRowCount(0)
        
        # Connect double-click signal
        table.cellDoubleClicked.connect(self.handle_job_double_click)
        
        return table
        
    def add_job_to_table(self, job_data):
        """Add a single job to the results table"""
        # Add job to data manager first
        job_id = self.data_manager.add_job(job_data)
        
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        
        # Add job data to columns
        self.results_table.setItem(row_position, 0, QTableWidgetItem(job_data.get('title', '')))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(job_data.get('company', '')))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(job_data.get('location', '')))
        self.results_table.setItem(row_position, 3, QTableWidgetItem(job_data.get('posted_date', '')))
        
        # Create status dropdown
        status_combo = QComboBox()
        status_combo.setObjectName("statusCombo")
        status_combo.addItems(self.data_manager.status_options)
        
        # Set current status from data manager
        current_job = self.data_manager.get_job(job_id)
        current_status = current_job.get('status', 'Not Reviewed') if current_job else 'Not Reviewed'
        status_index = status_combo.findText(current_status)
        if status_index >= 0:
            status_combo.setCurrentIndex(status_index)
        
        # Connect status change signal to data manager
        status_combo.currentTextChanged.connect(
            lambda status, job_id=job_id: self.handle_status_change(job_id, status)
        )
        
        # Add status dropdown to table
        self.results_table.setCellWidget(row_position, 4, status_combo)
        
        # Store row to job_id mapping for table operations
        if not hasattr(self, 'row_to_job_id'):
            self.row_to_job_id = {}
        self.row_to_job_id[row_position] = job_id
        
    def populate_results_table(self, jobs_list):
        """Populate the table with a list of jobs"""
        # Clear existing data
        self.clear_results_table()
        
        # Add jobs to data manager first
        self.data_manager.add_jobs(jobs_list)
        
        # Add each job to the table
        for job_data in jobs_list:
            self.add_job_to_table(job_data)
            
    def clear_results_table(self):
        """Clear all data from the results table"""
        self.results_table.setRowCount(0)
        self.data_manager.clear_data()
        if hasattr(self, 'row_to_job_id'):
            self.row_to_job_id.clear()
            
    def handle_status_change(self, job_id, new_status):
        """Handle status dropdown change for a job"""
        # Update status in data manager
        if self.data_manager.update_job_status(job_id, new_status):
            # Get updated job data for feedback
            job_data = self.data_manager.get_job(job_id)
            if job_data:
                job_title = job_data.get('title', 'Job')
                self.statusBar().showMessage(f"Status updated: {job_title} - {new_status}")
            else:
                self.statusBar().showMessage(f"Status updated to: {new_status}")
        else:
            self.statusBar().showMessage("Failed to update job status")
            
    def get_all_jobs_data(self):
        """Get all job data including current status for export"""
        return self.data_manager.get_jobs_for_export()
        
    def add_sample_data(self):
        """Add sample job data to demonstrate table functionality"""
        sample_jobs = [
            {
                'id': 'job_1',
                'title': 'Senior Software Engineer',
                'company': 'Tech Corp',
                'location': 'San Francisco, CA',
                'posted_date': '2 days ago',
                'status': 'Not Reviewed',
                'description': 'We are looking for a senior software engineer...',
                'url': 'https://linkedin.com/jobs/sample1'
            },
            {
                'id': 'job_2', 
                'title': 'Data Scientist',
                'company': 'Analytics Inc',
                'location': 'New York, NY',
                'posted_date': '1 week ago',
                'status': 'Interested',
                'description': 'Join our data science team...',
                'url': 'https://linkedin.com/jobs/sample2'
            },
            {
                'id': 'job_3',
                'title': 'Product Manager',
                'company': 'StartupXYZ',
                'location': 'Remote',
                'posted_date': '3 days ago', 
                'status': 'Applied',
                'description': 'Lead product development...',
                'url': 'https://linkedin.com/jobs/sample3'
            }
        ]
        
        self.populate_results_table(sample_jobs)
        
    def handle_job_double_click(self, row, column):
        """Handle double-click on job row to show details"""
        if hasattr(self, 'row_to_job_id') and row in self.row_to_job_id:
            job_id = self.row_to_job_id[row]
            job_data = self.data_manager.get_job(job_id)
            if job_data:
                self.show_job_details(job_data)
            
    def show_job_details(self, job_data):
        """Show job details in a popup dialog"""
        dialog = JobDetailsDialog(job_data, self)
        dialog.exec_()
        
    def setup_status_bar(self):
        """Create and configure the status bar"""
        status_bar = QStatusBar()
        status_bar.setObjectName("statusBar")
        
        # Default status message
        status_bar.showMessage("Ready to search LinkedIn jobs")
        
        self.setStatusBar(status_bar)
        
    def apply_styling(self):
        """Apply professional color scheme and styling"""
        # Main window styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {config.COLORS['background']};
            }}
            
            /* Header Styling */
            #headerFrame {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {config.COLORS['primary']}, 
                    stop: 1 #005885);
                border: none;
                border-bottom: 2px solid {config.COLORS['accent']};
            }}
            
            #titleLabel {{
                color: {config.COLORS['secondary']};
                background: transparent;
            }}
            
            #subtitleLabel {{
                color: #E6F3FF;
                background: transparent;
            }}
            
            /* Section Titles */
            #sectionTitle {{
                color: {config.COLORS['text']};
                background: transparent;
                padding: 5px 0px;
                border-bottom: 2px solid {config.COLORS['accent']};
                margin-bottom: 10px;
            }}
            
            /* Panel Styling */
            #searchFrame {{
                background-color: {config.COLORS['secondary']};
                border: 1px solid {config.COLORS['border']};
                border-radius: 8px;
                margin: 10px;
            }}
            
            #resultsFrame {{
                background-color: {config.COLORS['secondary']};
                border: 1px solid {config.COLORS['border']};
                border-radius: 8px;
                margin: 10px;
            }}
            
            /* Status Bar */
            #statusBar {{
                background-color: {config.COLORS['background']};
                border-top: 1px solid {config.COLORS['border']};
                color: {config.COLORS['text']};
                padding: 5px;
            }}
            
            /* Placeholder Text */
            #placeholderText {{
                color: #999999;
                font-size: 11px;
            }}
            
            /* Input Field Styling */
            #inputLabel {{
                color: {config.COLORS['text']};
                font-weight: bold;
                font-size: 11px;
                padding: 5px 0px;
            }}
            
            QLineEdit {{
                padding: 8px 12px;
                border: 2px solid {config.COLORS['border']};
                border-radius: 6px;
                background-color: {config.COLORS['secondary']};
                color: {config.COLORS['text']};
                font-size: 11px;
                min-height: 20px;
            }}
            
            QLineEdit:focus {{
                border-color: {config.COLORS['primary']};
                background-color: #F8FBFF;
            }}
            
            QLineEdit:hover {{
                border-color: {config.COLORS['accent']};
            }}
            
            /* ComboBox Styling */
            QComboBox {{
                padding: 8px 12px;
                border: 2px solid {config.COLORS['border']};
                border-radius: 6px;
                background-color: {config.COLORS['secondary']};
                color: {config.COLORS['text']};
                font-size: 11px;
                min-height: 20px;
                min-width: 120px;
            }}
            
            QComboBox:focus {{
                border-color: {config.COLORS['primary']};
                background-color: #F8FBFF;
            }}
            
            QComboBox:hover {{
                border-color: {config.COLORS['accent']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {config.COLORS['text']};
                margin-right: 5px;
            }}
            
            QComboBox QAbstractItemView {{
                border: 2px solid {config.COLORS['border']};
                background-color: {config.COLORS['secondary']};
                selection-background-color: {config.COLORS['accent']};
                selection-color: {config.COLORS['secondary']};
            }}
            
            /* Button Styling */
            QPushButton {{
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                min-width: 100px;
            }}
            
            #searchButton {{
                background-color: {config.COLORS['primary']};
                color: {config.COLORS['secondary']};
            }}
            
            #searchButton:hover {{
                background-color: #005885;
            }}
            
            #searchButton:pressed {{
                background-color: #004466;
            }}
            
            #clearButton {{
                background-color: #F5F5F5;
                color: {config.COLORS['text']};
                border: 2px solid {config.COLORS['border']};
            }}
            
            #clearButton:hover {{
                background-color: #E8E8E8;
                border-color: {config.COLORS['accent']};
            }}
            
            #clearButton:pressed {{
                background-color: #DDDDDD;
            }}
            
            /* Splitter Styling */
            QSplitter::handle {{
                background-color: {config.COLORS['border']};
                height: 2px;
            }}
            
            QSplitter::handle:hover {{
                background-color: {config.COLORS['accent']};
            }}
            
            /* Results Table Styling */
            #resultsTable {{
                background-color: {config.COLORS['secondary']};
                border: 1px solid {config.COLORS['border']};
                border-radius: 6px;
                gridline-color: {config.COLORS['border']};
                selection-background-color: #E6F3FF;
                selection-color: {config.COLORS['text']};
                font-size: 11px;
            }}
            
            #resultsTable::item {{
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
            }}
            
            #resultsTable::item:selected {{
                background-color: #E6F3FF;
                color: {config.COLORS['text']};
            }}
            
            #resultsTable::item:hover {{
                background-color: #F8FBFF;
            }}
            
            /* Table Header Styling */
            #resultsTable QHeaderView::section {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #F8F9FA, stop: 1 #E9ECEF);
                border: 1px solid {config.COLORS['border']};
                border-left: none;
                border-right: none;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 11px;
                color: {config.COLORS['text']};
            }}
            
            #resultsTable QHeaderView::section:first {{
                border-left: 1px solid {config.COLORS['border']};
                border-top-left-radius: 6px;
            }}
            
            #resultsTable QHeaderView::section:last {{
                border-right: 1px solid {config.COLORS['border']};
                border-top-right-radius: 6px;
            }}
            
            #resultsTable QHeaderView::section:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #E6F3FF, stop: 1 #CCE7FF);
            }}
            
            /* Alternating row colors */
            #resultsTable::item:alternate {{
                background-color: #FAFBFC;
            }}
            
            /* Progress Bar Styling */
            #progressBar {{
                border: 2px solid {config.COLORS['border']};
                border-radius: 6px;
                background-color: {config.COLORS['secondary']};
                text-align: center;
                font-size: 10px;
                font-weight: bold;
                color: {config.COLORS['text']};
                min-height: 20px;
            }}
            
            #progressBar::chunk {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {config.COLORS['primary']}, 
                    stop: 1 #005885);
                border-radius: 4px;
                margin: 1px;
            }}
            
            /* Progress Label Styling */
            #progressLabel {{
                color: {config.COLORS['text']};
                font-size: 10px;
                font-style: italic;
                padding: 2px 0px;
                margin-top: 5px;
            }}
            
            /* Status ComboBox in Table */
            #statusCombo {{
                border: 1px solid {config.COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                background-color: {config.COLORS['secondary']};
                font-size: 10px;
                min-height: 16px;
            }}
            
            #statusCombo:focus {{
                border-color: {config.COLORS['primary']};
            }}
            
            #statusCombo::drop-down {{
                border: none;
                width: 16px;
            }}
            
            #statusCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {config.COLORS['text']};
                margin-right: 3px;
            }}
            
            #statusCombo QAbstractItemView {{
                border: 1px solid {config.COLORS['border']};
                background-color: {config.COLORS['secondary']};
                selection-background-color: {config.COLORS['accent']};
                selection-color: {config.COLORS['secondary']};
                font-size: 10px;
            }}
            
            /* Results Filter Panel Styling */
            #resultsFilterFrame {{
                background-color: #F8F9FA;
                border: 1px solid {config.COLORS['border']};
                border-radius: 6px;
                margin-bottom: 10px;
            }}
            
            #filterLabel {{
                color: {config.COLORS['text']};
                font-size: 10px;
                font-weight: bold;
            }}
            
            #resultsSearchInput {{
                padding: 6px 10px;
                border: 2px solid {config.COLORS['border']};
                border-radius: 4px;
                background-color: {config.COLORS['secondary']};
                color: {config.COLORS['text']};
                font-size: 10px;
                min-height: 16px;
            }}
            
            #resultsSearchInput:focus {{
                border-color: {config.COLORS['primary']};
                background-color: #F8FBFF;
            }}
            
            #statusFilterCombo {{
                padding: 6px 10px;
                border: 2px solid {config.COLORS['border']};
                border-radius: 4px;
                background-color: {config.COLORS['secondary']};
                color: {config.COLORS['text']};
                font-size: 10px;
                min-height: 16px;
            }}
            
            #statusFilterCombo:focus {{
                border-color: {config.COLORS['primary']};
                background-color: #F8FBFF;
            }}
            
            #statusFilterCombo::drop-down {{
                border: none;
                width: 18px;
            }}
            
            #statusFilterCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {config.COLORS['text']};
                margin-right: 4px;
            }}
            
            #statusFilterCombo QAbstractItemView {{
                border: 2px solid {config.COLORS['border']};
                background-color: {config.COLORS['secondary']};
                selection-background-color: {config.COLORS['accent']};
                selection-color: {config.COLORS['secondary']};
                font-size: 10px;
            }}
            
            #clearResultsFiltersButton {{
                background-color: #F5F5F5;
                color: {config.COLORS['text']};
                border: 2px solid {config.COLORS['border']};
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                min-height: 16px;
            }}
            
            #clearResultsFiltersButton:hover {{
                background-color: #E8E8E8;
                border-color: {config.COLORS['accent']};
            }}
            
            #clearResultsFiltersButton:pressed {{
                background-color: #DDDDDD;
            }}
        """)


class JobDetailsDialog(QDialog):
    """Dialog for displaying detailed job information"""
    
    def __init__(self, job_data, parent=None):
        super().__init__(parent)
        self.job_data = job_data
        self.setup_dialog()
        self.populate_data()
        
    def setup_dialog(self):
        """Set up the dialog window and layout"""
        self.setWindowTitle("Job Details")
        self.setModal(True)
        self.resize(600, 500)
        self.setMinimumSize(500, 400)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Job title and company header
        header_frame = QFrame()
        header_frame.setObjectName("jobDetailsHeader")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        self.title_label = QLabel()
        self.title_label.setObjectName("jobDetailsTitle")
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        
        self.company_label = QLabel()
        self.company_label.setObjectName("jobDetailsCompany")
        company_font = QFont("Segoe UI", 12)
        self.company_label.setFont(company_font)
        
        self.location_label = QLabel()
        self.location_label.setObjectName("jobDetailsLocation")
        location_font = QFont("Segoe UI", 10)
        self.location_label.setFont(location_font)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.company_label)
        header_layout.addWidget(self.location_label)
        
        layout.addWidget(header_frame)
        
        # Job description
        desc_label = QLabel("Job Description:")
        desc_label.setObjectName("sectionLabel")
        desc_font = QFont("Segoe UI", 11, QFont.Bold)
        desc_label.setFont(desc_font)
        layout.addWidget(desc_label)
        
        self.description_text = QTextEdit()
        self.description_text.setObjectName("jobDescription")
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(200)
        layout.addWidget(self.description_text)
        
        # Job details
        details_label = QLabel("Details:")
        details_label.setObjectName("sectionLabel")
        details_label.setFont(desc_font)
        layout.addWidget(details_label)
        
        details_frame = QFrame()
        details_layout = QGridLayout(details_frame)
        details_layout.setSpacing(10)
        
        # Posted date
        posted_label = QLabel("Posted:")
        posted_label.setObjectName("detailLabel")
        self.posted_value = QLabel()
        self.posted_value.setObjectName("detailValue")
        
        # Status
        status_label = QLabel("Status:")
        status_label.setObjectName("detailLabel")
        self.status_value = QLabel()
        self.status_value.setObjectName("detailValue")
        
        details_layout.addWidget(posted_label, 0, 0)
        details_layout.addWidget(self.posted_value, 0, 1)
        details_layout.addWidget(status_label, 1, 0)
        details_layout.addWidget(self.status_value, 1, 1)
        
        details_layout.setColumnStretch(1, 1)
        layout.addWidget(details_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.linkedin_button = QPushButton("View on LinkedIn")
        self.linkedin_button.setObjectName("linkedinButton")
        self.linkedin_button.clicked.connect(self.open_linkedin_url)
        
        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.linkedin_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Apply styling
        self.apply_dialog_styling()
        
    def populate_data(self):
        """Populate the dialog with job data"""
        self.title_label.setText(self.job_data.get('title', 'No Title'))
        self.company_label.setText(self.job_data.get('company', 'No Company'))
        self.location_label.setText(self.job_data.get('location', 'No Location'))
        
        description = self.job_data.get('description', 'No description available.')
        self.description_text.setPlainText(description)
        
        self.posted_value.setText(self.job_data.get('posted_date', 'Unknown'))
        self.status_value.setText(self.job_data.get('status', 'Not Reviewed'))
        
    def open_linkedin_url(self):
        """Open the LinkedIn job posting in the default browser"""
        url = self.job_data.get('url', '')
        if url:
            QDesktopServices.openUrl(QUrl(url))
        else:
            # Show message if no URL available
            self.parent().statusBar().showMessage("No LinkedIn URL available for this job")
            
    def apply_dialog_styling(self):
        """Apply styling to the dialog"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {config.COLORS['background']};
            }}
            
            #jobDetailsHeader {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {config.COLORS['primary']}, 
                    stop: 1 #005885);
                border-radius: 8px;
                margin-bottom: 10px;
            }}
            
            #jobDetailsTitle {{
                color: {config.COLORS['secondary']};
                background: transparent;
            }}
            
            #jobDetailsCompany {{
                color: #E6F3FF;
                background: transparent;
            }}
            
            #jobDetailsLocation {{
                color: #CCE7FF;
                background: transparent;
            }}
            
            #sectionLabel {{
                color: {config.COLORS['text']};
                padding: 5px 0px;
                border-bottom: 2px solid {config.COLORS['accent']};
                margin-bottom: 5px;
            }}
            
            #jobDescription {{
                border: 2px solid {config.COLORS['border']};
                border-radius: 6px;
                background-color: {config.COLORS['secondary']};
                color: {config.COLORS['text']};
                font-size: 11px;
                padding: 10px;
            }}
            
            #detailLabel {{
                color: {config.COLORS['text']};
                font-weight: bold;
                font-size: 11px;
            }}
            
            #detailValue {{
                color: {config.COLORS['text']};
                font-size: 11px;
            }}
            
            #linkedinButton {{
                background-color: {config.COLORS['primary']};
                color: {config.COLORS['secondary']};
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                min-width: 120px;
            }}
            
            #linkedinButton:hover {{
                background-color: #005885;
            }}
            
            #linkedinButton:pressed {{
                background-color: #004466;
            }}
            
            #closeButton {{
                background-color: #F5F5F5;
                color: {config.COLORS['text']};
                border: 2px solid {config.COLORS['border']};
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                min-width: 80px;
            }}
            
            #closeButton:hover {{
                background-color: #E8E8E8;
                border-color: {config.COLORS['accent']};
            }}
            
            #closeButton:pressed {{
                background-color: #DDDDDD;
            }}
        """)