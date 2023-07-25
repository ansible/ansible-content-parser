% include("head.tpl")

<div class="container">
  <div class="row">
    <table id="example" class="table table-striped table-bordered" cellspacing="0" width="100%">
      <thead>
      <tr>
        <th>Moudule Name</th>
        <th>Count</th>
      </tr>
      </thead>
      <tbody role="rowgroup">
      % for moduleName,count in summary:
      <tr role="row">
        <td>{{ moduleName }}</td>
        <td>{{ count }}</td>
      </tr>
      % end
      </tbody>
    </table>
  </div>
</div>

<script>
  $(document).ready(function() {
  $("#example").DataTable({
    "pageLength": 25,
    "order": [[ 1, 'desc' ],[ 0, 'asc' ]]
  });
});
</script>