% include("head.tpl")

<div class="container">
  <div class="row">
    <form id="myForm" action="/run" method="post">
      <div class="form-group">
        Repository URL:
        <input type="text" class="form-control" name="url" type="Repository URL" autofocus="autofocus"/>
        <div class="form-check">
          <input class="form-check-input" type="checkbox" name="clear_work_dir" checked id="check1">
          <label class="form-check-label" for="check1">
            Remove all files in the work directory
          </label>
        </div>
      </div>
      <input id="submit_btn" class="btn btn-primary" value="Run" type="submit"/>
      <button id="spinner" class="btn btn-primary" type="button" style="display: none;">
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Processing...
      </button>
    </form>
  </div>
</div>

<script>
function display_spinner() {
  $("#submit_btn").hide();
  $("#spinner").show();
}

const form = document.getElementById("myForm");
form.addEventListener("submit", display_spinner);


</script>
