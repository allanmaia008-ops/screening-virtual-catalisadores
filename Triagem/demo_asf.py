"""Generate a reproducible ASF example without running external databases."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from asf import distribution, aviation_screen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--alpha', type=float, default=.85)
    args = parser.parse_args()
    result = distribution(args.alpha)
    result['aviation_screen'] = aviation_screen(args.alpha)
    args.output.mkdir(parents=True, exist_ok=True)
    stem = 'distribuicao_ASF_FT_alpha_' + str(args.alpha).replace('.', '_')
    (args.output / (stem+'.json')).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout='constrained')
    axes[0].bar([r['carbon_number'] for r in result['rows']], [100*r['fraction'] for r in result['rows']], color='#147d64')
    axes[0].set(xlabel='Número de carbonos', ylabel='Fração de carbono (%)', title=f'ASF ideal | alpha = {args.alpha:g}')
    for a in (.7, .85, .95):
        data = aviation_screen(a)
        axes[1].plot(['C1-C7', 'C8-C16', 'C17+'], [100*data[k] for k in ('lighter_fraction','direct_cut_fraction','heavy_feed_fraction')], marker='o', label=f'alpha = {a}')
    axes[1].set(ylabel='Fração de carbono (%)', title='Cortes para estudo FT-Aviação')
    axes[1].legend()
    fig.supxlabel('Alpha informado; distribuição condicional aos hidrocarbonetos. C8-C16 não implica qualificação SAF.', fontsize=9)
    fig.savefig(args.output / (stem+'.png'), dpi=170)
    plt.close(fig)
    print(json.dumps({'groups':result['exclusive_groups'], 'C5+':result['C5plus_subtotal'], 'closure_error':result['closure_error'], 'output':str(args.output)}, ensure_ascii=False))


if __name__ == '__main__': main()
