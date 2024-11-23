import React, { useState } from "react";

const TopBar = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState("");

  // Handle search form submit
  const handleSearch = (event) => {
    event.preventDefault(); // Prevent the default form submission
    onSearch(searchTerm);   // Pass the search term to the parent component (App)
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
      <div className="container-fluid">
        <a className="navbar-brand" href="/">
          Bird View
        </a>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto">
            <li className="nav-item">
              <a className="nav-link active" aria-current="page" href="/">Home</a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/about">About</a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/contact">Contact</a>
            </li>
            <li className="nav-item">
              <form className="d-flex" onSubmit={handleSearch}>
                <input
                  className="form-control me-2"
                  type="search"
                  placeholder="Search Stocks..."
                  aria-label="Search"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)} // Update search term as the user types
                />
                <button className="btn btn-outline-success" type="submit">Search</button>
              </form>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default TopBar;
