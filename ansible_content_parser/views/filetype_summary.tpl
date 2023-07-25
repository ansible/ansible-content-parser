% include("head.tpl")

<div class="container">
  <div class="row">
    <table id="example" class="table table-striped table-bordered" cellspacing="0" width="100%">
      <thead>
      <tr>
        <th>File Type</th>
        <th>Count</th>
      </tr>
      </thead>
      <tbody role="rowgroup">
      % for fileType,count in summary:
      <tr role="row">
        % if fileType in ['playbook', 'tasks', 'jinja2', 'vars', 'handlers']:
          <td><span class="badge badge-{{ fileType }}">{{ fileType }}</span></td>
        % else:
          <td><span class="badge badge-default">{{ fileType }}</span></td>
        % end
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