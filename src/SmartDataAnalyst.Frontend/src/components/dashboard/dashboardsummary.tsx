// import type { DatasetSummar } from "../../api/dashboardApi";

// export function DashboardSummary({ summary }: { summary: DatasetSummary }) {
//   //alert(JSON.stringify(summary.summary));
//   return (
//     <div className="dashboard-summary">
//       <section>
//         <h2>Dataset Overview</h2>
//         <p>
//           <pre>{JSON.stringify(summary.summary, null, 2)}</pre>
//         </p>
//       </section>
//       {summary.insights && summary.insights.length > 0 && (
//         <section>
//           <h3>Key Insights</h3>
//           <ul>
//             {summary.insights.map((insight, index) => (
//               <li key={index}>{insight}</li>
//             ))}
//           </ul>
//         </section>
//       )}

//       {summary.warnings && summary.warnings.length > 0 && (
//         <section>
//           <h3>Data Quality Warnings</h3>
//           <ul>
//             {summary.warnings.map((warning, index) => (
//               <li key={index}>{warning}</li>
//             ))}
//           </ul>
//         </section>
//       )}
//     </div>
//   );
// }

import type { DatasetSummaryResponse } from "../../api/dashboardApi";

export function DashboardSummary({
  summary,
}: {
  summary: DatasetSummaryResponse;
}) {
  const data = summary.summary;

  return (
    <div className="dashboard-summary">
      <section>
        <h2>Dataset Overview</h2>

        <p>
          <strong>File:</strong> {data.file_name}
        </p>
        <p>
          <strong>Rows:</strong> {data.rows}
        </p>
        <p>
          <strong>Columns:</strong> {data.columns}
        </p>
      </section>

      <section>
        <h3>Columns Info</h3>
        <pre>{JSON.stringify(data.columns_info, null, 2)}</pre>
      </section>

      <section>
        <h3>Numeric Summary</h3>
        <pre>{JSON.stringify(data.numeric_summary, null, 2)}</pre>
      </section>
    </div>
  );
}
