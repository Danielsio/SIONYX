using Xunit.Abstractions;
using Xunit.Sdk;

namespace SionyxKiosk.E2E.Fixtures;

public class PriorityOrderer : ITestCaseOrderer
{
    public IEnumerable<TTestCase> OrderTestCases<TTestCase>(IEnumerable<TTestCase> testCases)
        where TTestCase : ITestCase
    {
        var sorted = new SortedDictionary<int, List<TTestCase>>();

        foreach (var testCase in testCases)
        {
            var priority = testCase.TestMethod.Method
                .GetCustomAttributes(typeof(TestPriorityAttribute).AssemblyQualifiedName)
                .FirstOrDefault()
                ?.GetNamedArgument<int>("Priority") ?? int.MaxValue;

            if (!sorted.ContainsKey(priority))
                sorted[priority] = new List<TTestCase>();

            sorted[priority].Add(testCase);
        }

        foreach (var kvp in sorted)
            foreach (var testCase in kvp.Value)
                yield return testCase;
    }
}
