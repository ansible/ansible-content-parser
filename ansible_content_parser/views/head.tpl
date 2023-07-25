<head>
	<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.5/css/jquery.dataTables.min.css">
	<link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css">
	<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.5/css/dataTables.bootstrap5.min.css">
	<script type="text/javascript" language="javascript" src="https://code.jquery.com/jquery-3.7.0.js"></script>
	<script type="text/javascript" language="javascript" src="https://cdn.datatables.net/1.13.5/js/jquery.dataTables.min.js"></script>
	<script type="text/javascript" language="javascript" src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</head>

<style>

.badge-playbook {
   --bs-badge-font-size: 0.9em;
   color: white;
   background-color: darkred;
}

.badge-tasks {
   --bs-badge-font-size: 0.9em;
   color: white;
   background-color: orangered;
}

.badge-jinja2 {
   --bs-badge-font-size: 0.9em;
   color: white;
   background-color: blue;
}

.badge-vars {
   --bs-badge-font-size: 0.9em;
   color: white;
   background-color: green;
}

.badge-handlers {
   --bs-badge-font-size: 0.9em;
   color: white;
   background-color: indigo;
}

.badge-default {
   --bs-badge-font-size: 0.9em;
   color: black;
   background-color: lightgray;
}

</style>

<nav class="navbar navbar-expand-lg bg-light">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Ansible Content Parser</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav">
        <li class="nav-item">
          <a class="nav-link active" aria-current="page" href="/">New ansible-lint run</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/files">Files found</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/matches">Lint errors</a>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
            Analysis
          </a>
          <div class="dropdown-menu" aria-labelledby="navbarDropdown">
            <a class="dropdown-item" href="/analysis-filetype-summary">File Type Summary</a>
            <a class="dropdown-item" href="/analysis-module-summary">Modules Summary</a>
            <!-- Hide this for the moment
            <a class="dropdown-item" href="/analysis-dependency-graph">Dependency Graph</a>
            -->
          </div>
        </li>
      </ul>
    </div>
  </div>
</nav>