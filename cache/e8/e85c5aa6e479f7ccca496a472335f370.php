<?php

use Twig\Environment;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Extension\CoreExtension;
use Twig\Extension\SandboxExtension;
use Twig\Markup;
use Twig\Sandbox\SecurityError;
use Twig\Sandbox\SecurityNotAllowedTagError;
use Twig\Sandbox\SecurityNotAllowedFilterError;
use Twig\Sandbox\SecurityNotAllowedFunctionError;
use Twig\Source;
use Twig\Template;
use Twig\TemplateWrapper;

/* tables/embedding_table.html.twig */
class __TwigTemplate_1322fea2b282187e2bbbfa370803e7a4 extends Template
{
    private Source $source;
    /**
     * @var array<string, Template>
     */
    private array $macros = [];

    public function __construct(Environment $env)
    {
        parent::__construct($env);

        $this->source = $this->getSourceContext();

        $this->parent = false;

        $this->blocks = [
        ];
    }

    protected function doDisplay(array $context, array $blocks = []): iterable
    {
        $macros = $this->macros;
        // line 1
        yield "<table class=\"table table-hover\">
    <thead class=\"table-light sticky-top\">
    <tr>
        <th scope=\"col\">#</th>
        <th scope=\"col\">Profil-ID</th>
        <th scope=\"col\">Name</th>
        <th scope=\"col\" class=\"text-end\">Vektorbetrag</th>
        <th scope=\"col\" class=\"text-end\">AVG-Vektorbetrag</th>
        <th scope=\"col\" class=\"text-end\">Abstand zum AVG</th>
        <th scope=\"col\" class=\"text-end\">Vektor erstellt</th>
        <th scope=\"col\" class=\"text-end\">Aktionen</th>
    </tr>
    </thead>
    <tbody class=\"table-group-divider\">
    ";
        // line 15
        $context['_parent'] = $context;
        $context['_seq'] = CoreExtension::ensureTraversable(($context["items"] ?? null));
        $context['loop'] = [
          'parent' => $context['_parent'],
          'index0' => 0,
          'index'  => 1,
          'first'  => true,
        ];
        if (is_array($context['_seq']) || (is_object($context['_seq']) && $context['_seq'] instanceof \Countable)) {
            $length = count($context['_seq']);
            $context['loop']['revindex0'] = $length - 1;
            $context['loop']['revindex'] = $length;
            $context['loop']['length'] = $length;
            $context['loop']['last'] = 1 === $length;
        }
        foreach ($context['_seq'] as $context["_key"] => $context["speaker"]) {
            // line 16
            yield "        <tr>
            <th class=\"align-content-center\" scope=\"row\">";
            // line 17
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(CoreExtension::getAttribute($this->env, $this->source, $context["loop"], "index", [], "any", false, false, false, 17), "html", null, true);
            yield "</th>
            <td class=\"align-content-center\">";
            // line 18
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(CoreExtension::getAttribute($this->env, $this->source, $context["speaker"], "profile_id", [], "any", false, false, false, 18), "html", null, true);
            yield "</td>
            <td class=\"align-content-center\">";
            // line 19
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(CoreExtension::getAttribute($this->env, $this->source, $context["speaker"], "name", [], "any", false, false, false, 19), "html", null, true);
            yield "</td>
            <td class=\"text-end align-content-center\"><div class=\"\">";
            // line 20
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($this->extensions['Twig\Extension\CoreExtension']->formatNumber(CoreExtension::getAttribute($this->env, $this->source, $context["speaker"], "embedding_length", [], "any", false, false, false, 20), 4, ",", ""), "html", null, true);
            yield "</div></td>
            <td class=\"text-end align-content-center\"><div class=\"\">";
            // line 21
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($this->extensions['Twig\Extension\CoreExtension']->formatNumber(CoreExtension::getAttribute($this->env, $this->source, $context["speaker"], "embedding_avg", [], "any", false, false, false, 21), 4, ",", ""), "html", null, true);
            yield "</div></td>
            <td class=\"text-end align-content-center\"><div class=\"\">";
            // line 22
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($this->extensions['Twig\Extension\CoreExtension']->formatNumber(CoreExtension::getAttribute($this->env, $this->source, $context["speaker"], "angle", [], "any", false, false, false, 22), 4, ",", ""), "html", null, true);
            yield "</div></td>
            <td class=\"text-end align-content-center\">";
            // line 23
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($this->extensions['Twig\Extension\CoreExtension']->formatDate(CoreExtension::getAttribute($this->env, $this->source, $context["speaker"], "created", [], "any", false, false, false, 23), "d.m.Y H:i"), "html", null, true);
            yield " Uhr</td>
            <td class=\"text-end align-content-center\"><a href=\"/?controller=app&view=show_profiles&name=";
            // line 24
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(Twig\Extension\CoreExtension::urlencode(CoreExtension::getAttribute($this->env, $this->source, $context["speaker"], "name", [], "any", false, false, false, 24)), "html", null, true);
            yield "\" class=\"btn btn-sm btn-primary\"><i class=\"ti ti-users me-1\"></i>Profile anzeigen</a></td>
        </tr>
    ";
            ++$context['loop']['index0'];
            ++$context['loop']['index'];
            $context['loop']['first'] = false;
            if (isset($context['loop']['revindex0'], $context['loop']['revindex'])) {
                --$context['loop']['revindex0'];
                --$context['loop']['revindex'];
                $context['loop']['last'] = 0 === $context['loop']['revindex0'];
            }
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_key'], $context['speaker'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 27
        yield "    </tbody>
</table>";
        yield from [];
    }

    /**
     * @codeCoverageIgnore
     */
    public function getTemplateName(): string
    {
        return "tables/embedding_table.html.twig";
    }

    /**
     * @codeCoverageIgnore
     */
    public function isTraitable(): bool
    {
        return false;
    }

    /**
     * @codeCoverageIgnore
     */
    public function getDebugInfo(): array
    {
        return array (  123 => 27,  106 => 24,  102 => 23,  98 => 22,  94 => 21,  90 => 20,  86 => 19,  82 => 18,  78 => 17,  75 => 16,  58 => 15,  42 => 1,);
    }

    public function getSourceContext(): Source
    {
        return new Source("<table class=\"table table-hover\">
    <thead class=\"table-light sticky-top\">
    <tr>
        <th scope=\"col\">#</th>
        <th scope=\"col\">Profil-ID</th>
        <th scope=\"col\">Name</th>
        <th scope=\"col\" class=\"text-end\">Vektorbetrag</th>
        <th scope=\"col\" class=\"text-end\">AVG-Vektorbetrag</th>
        <th scope=\"col\" class=\"text-end\">Abstand zum AVG</th>
        <th scope=\"col\" class=\"text-end\">Vektor erstellt</th>
        <th scope=\"col\" class=\"text-end\">Aktionen</th>
    </tr>
    </thead>
    <tbody class=\"table-group-divider\">
    {% for speaker in items %}
        <tr>
            <th class=\"align-content-center\" scope=\"row\">{{ loop.index }}</th>
            <td class=\"align-content-center\">{{ speaker.profile_id }}</td>
            <td class=\"align-content-center\">{{ speaker.name }}</td>
            <td class=\"text-end align-content-center\"><div class=\"\">{{ speaker.embedding_length|number_format(4, ',', '')  }}</div></td>
            <td class=\"text-end align-content-center\"><div class=\"\">{{ speaker.embedding_avg|number_format(4, ',', '')  }}</div></td>
            <td class=\"text-end align-content-center\"><div class=\"\">{{ speaker.angle|number_format(4, ',', '')  }}</div></td>
            <td class=\"text-end align-content-center\">{{ speaker.created|date('d.m.Y H:i') }} Uhr</td>
            <td class=\"text-end align-content-center\"><a href=\"/?controller=app&view=show_profiles&name={{ speaker.name|url_encode }}\" class=\"btn btn-sm btn-primary\"><i class=\"ti ti-users me-1\"></i>Profile anzeigen</a></td>
        </tr>
    {% endfor %}
    </tbody>
</table>", "tables/embedding_table.html.twig", "C:\\Users\\BenjaminWagner\\PycharmProjects\\alumni-portal-analyse\\templates\\tables\\embedding_table.html.twig");
    }
}
